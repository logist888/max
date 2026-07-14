// Доступ сайта к артефакту графа профессий (build/graph/*.jsonl).
// Читаем только то, что нужно страницам /professiya/: профессии, их компетенции
// (авторитетно, ESCO) и курируемые связи с направлениями (гипотеза, помечается).

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { slugify } from '../pipeline/slugs.ts';

const BUILD = resolve(process.cwd(), 'build', 'graph');

interface RawNode {
  id: string; type: string; localIds: { scheme: string; value: string }[];
  labels: { ru?: string; en?: string }; status: string; confidence: number;
  attrs: Record<string, unknown>;
}
interface RawEdge {
  id: string; type: string; from: string; to: string; weight: number | null;
  confidence: number; method: string; status: string; explanation: string;
}

export interface Competency { label: string; kind: 'essential' | 'optional'; weight: number | null; }
export interface RouteLevel { level: string; slug: string; }
// Направление, ведущее к профессии; уровни (бакалавриат/специалитет/…) собраны
// в одну карточку — одноимённые коды разных уровней не дублируются.
export interface RouteDirection { name: string; confidence: number; note: string; levels: RouteLevel[]; }
export interface Salary {
  rosstatAvg: number | null; rosstatDate: string | null;
  trudvsemMedian: number | null; trudvsemP25: number | null; trudvsemP75: number | null;
  trudvsemCount: number | null; trudvsemDate: string | null;
}
export interface Profession {
  isco: string; slug: string; nameRu: string; nameEn: string; hasRuName: boolean;
  definitionEn: string; tasksEn: string; escoLabelsEn: string[];
  okzExamples: string[];
  parentIsco3: string; escoOccupationCount: number;
  competencies: Competency[];      // авторитетно (ESCO)
  routes: RouteDirection[];        // курируемо (гипотеза) — сопоставление, не факт
  salary: Salary | null;           // авторитетно (Росстат / Работа России)
}

function loadJsonl<T>(name: string): T[] {
  const text = readFileSync(resolve(BUILD, name), 'utf8');
  return text.split('\n').filter(Boolean).map((l) => JSON.parse(l) as T);
}

let cache: {
  professions: Profession[];
  bySlug: Map<string, Profession>;
  /** ОКСО направления → профессии, сопоставленные с ним (курируемо). */
  byDirectionOkso: Map<string, { slug: string; nameRu: string; confidence: number }[]>;
} | null = null;

export function graph() {
  if (cache) return cache;
  const nodes = loadJsonl<RawNode>('nodes.jsonl');
  const edges = loadJsonl<RawEdge>('edges.jsonl');

  const occ = nodes.filter((n) => n.type === 'Occupation');
  const compById = new Map(nodes.filter((n) => n.type === 'Competency').map((n) => [n.id, n]));
  const dirById = new Map(nodes.filter((n) => n.type === 'EducationDirection').map((n) => [n.id, n]));
  const salaryById = new Map(nodes.filter((n) => n.type === 'Salary').map((n) => [n.id, n]));

  // REQUIRES: профессия → компетенция; LEADS_TO: направление → профессия;
  // HAS_SALARY: профессия → зарплата
  const reqByOcc = new Map<string, RawEdge[]>();
  const routesByOcc = new Map<string, RawEdge[]>();
  const salaryByOcc = new Map<string, RawNode>();
  for (const e of edges) {
    if (e.type === 'REQUIRES') {
      (reqByOcc.get(e.from) ?? reqByOcc.set(e.from, []).get(e.from)!).push(e);
    } else if (e.type === 'LEADS_TO') {
      (routesByOcc.get(e.to) ?? routesByOcc.set(e.to, []).get(e.to)!).push(e);
    } else if (e.type === 'HAS_SALARY') {
      const s = salaryById.get(e.to);
      if (s) salaryByOcc.set(e.from, s);
    }
  }

  const professions: Profession[] = occ.map((o) => {
    const isco = o.id.split(':').pop()!;
    const nameRu = o.labels.ru ?? o.labels.en ?? isco;
    const nameEn = o.labels.en ?? '';
    const competencies: Competency[] = (reqByOcc.get(o.id) ?? [])
      .map((e) => ({
        label: compById.get(e.to)?.labels.en ?? '',
        kind: (e.weight ?? 0) >= 0.5 || e.explanation.includes('Ключевая') ? 'essential' as const : 'optional' as const,
        weight: e.weight,
      }))
      .filter((c) => c.label)
      .sort((a, b) => (b.weight ?? 0) - (a.weight ?? 0));
    // Группируем направления по названию: одно и то же поле на разных уровнях
    // (бакалавриат/специалитет/магистратура/зонтичный код) — одна карточка,
    // внутри — доступные уровни ссылками. Иначе одноимённые карточки дублируются.
    const LEVEL_ORDER = ['Бакалавриат', 'Специалитет', 'Магистратура',
      'Базовое высшее образование', 'Специализированное высшее образование', 'Аспирантура'];
    const grp = new Map<string, { name: string; confidence: number; note: string; levels: Map<string, string> }>();
    for (const e of routesByOcc.get(o.id) ?? []) {
      const d = dirById.get(e.from);
      const name = d?.labels.ru ?? '';
      const slug = (d?.attrs.slug as string) ?? '';
      const level = (d?.attrs.level as string) ?? '';
      if (!name || !slug) continue;
      const g = grp.get(name) ?? { name, confidence: e.confidence, note: e.explanation, levels: new Map() };
      g.confidence = Math.max(g.confidence, e.confidence);
      if (level && !g.levels.has(level)) g.levels.set(level, slug);
      grp.set(name, g);
    }
    const routes: RouteDirection[] = [...grp.values()].map((g) => ({
      name: g.name, confidence: g.confidence, note: g.note,
      levels: [...g.levels.entries()].map(([level, slug]) => ({ level, slug }))
        .sort((a, b) => ((LEVEL_ORDER.indexOf(a.level) + 99) % 99) - ((LEVEL_ORDER.indexOf(b.level) + 99) % 99)),
    })).sort((a, b) => b.confidence - a.confidence || a.name.localeCompare(b.name, 'ru'));

    const sNode = salaryByOcc.get(o.id);
    const salary: Salary | null = sNode ? {
      rosstatAvg: (sNode.attrs.rosstatAvg as number) ?? null,
      rosstatDate: (sNode.attrs.rosstatDate as string) ?? null,
      trudvsemMedian: (sNode.attrs.trudvsemMedian as number) ?? null,
      trudvsemP25: (sNode.attrs.trudvsemP25 as number) ?? null,
      trudvsemP75: (sNode.attrs.trudvsemP75 as number) ?? null,
      trudvsemCount: (sNode.attrs.trudvsemCount as number) ?? null,
      trudvsemDate: (sNode.attrs.trudvsemDate as string) ?? null,
    } : null;

    return {
      isco, slug: `${slugify(nameRu).slice(0, 60)}-${isco}`,
      nameRu, nameEn, hasRuName: !!o.labels.ru,
      definitionEn: (o.attrs.definitionEn as string) ?? '',
      tasksEn: (o.attrs.tasksEn as string) ?? '',
      escoLabelsEn: (o.attrs.escoLabelsEn as string[]) ?? [],
      okzExamples: (o.attrs.okzExamples as string[]) ?? [],
      parentIsco3: (o.attrs.parentIsco3 as string) ?? isco.slice(0, 3),
      escoOccupationCount: (o.attrs.escoOccupationCount as number) ?? 0,
      competencies, routes, salary,
    };
  }).sort((a, b) => a.nameRu.localeCompare(b.nameRu, 'ru'));

  const bySlug = new Map(professions.map((p) => [p.slug, p]));
  // Обратная карта: ОКСО направления → профессии. Строим прямо из рёбер LEADS_TO
  // (routes схлопнуты по названию и не хранят okso).
  const profByIsco = new Map(professions.map((p) => [p.isco, p]));
  const byDirectionOkso = new Map<string, { slug: string; nameRu: string; confidence: number }[]>();
  for (const e of edges) {
    if (e.type !== 'LEADS_TO') continue;
    const okso = e.from.replace('me:educationdirection:', '');
    const p = profByIsco.get(e.to.replace('me:occupation:', ''));
    if (!p) continue;
    const arr = byDirectionOkso.get(okso) ?? [];
    arr.push({ slug: p.slug, nameRu: p.nameRu, confidence: e.confidence });
    byDirectionOkso.set(okso, arr);
  }
  for (const arr of byDirectionOkso.values()) arr.sort((a, b) => b.confidence - a.confidence);
  cache = { professions, bySlug, byDirectionOkso };
  return cache;
}
