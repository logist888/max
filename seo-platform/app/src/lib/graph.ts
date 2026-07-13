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
export interface RouteDirection { okso: string; name: string; slug: string; confidence: number; note: string; }
export interface Profession {
  isco: string; slug: string; nameRu: string; nameEn: string; hasRuName: boolean;
  definitionEn: string; tasksEn: string; escoLabelsEn: string[];
  parentIsco3: string; escoOccupationCount: number;
  competencies: Competency[];      // авторитетно (ESCO)
  routes: RouteDirection[];        // курируемо (гипотеза) — сопоставление, не факт
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

  // REQUIRES: профессия → компетенция; LEADS_TO: направление → профессия
  const reqByOcc = new Map<string, RawEdge[]>();
  const routesByOcc = new Map<string, RawEdge[]>();
  for (const e of edges) {
    if (e.type === 'REQUIRES') {
      (reqByOcc.get(e.from) ?? reqByOcc.set(e.from, []).get(e.from)!).push(e);
    } else if (e.type === 'LEADS_TO') {
      (routesByOcc.get(e.to) ?? routesByOcc.set(e.to, []).get(e.to)!).push(e);
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
    const routes: RouteDirection[] = (routesByOcc.get(o.id) ?? []).map((e) => {
      const d = dirById.get(e.from);
      return {
        okso: d?.localIds.find((l) => l.scheme === 'okso')?.value ?? '',
        name: d?.labels.ru ?? '',
        slug: (d?.attrs.slug as string) ?? '',
        confidence: e.confidence,
        note: e.explanation,
      };
    }).filter((r) => r.name && r.slug).sort((a, b) => b.confidence - a.confidence);

    return {
      isco, slug: `${slugify(nameRu).slice(0, 60)}-${isco}`,
      nameRu, nameEn, hasRuName: !!o.labels.ru,
      definitionEn: (o.attrs.definitionEn as string) ?? '',
      tasksEn: (o.attrs.tasksEn as string) ?? '',
      escoLabelsEn: (o.attrs.escoLabelsEn as string[]) ?? [],
      parentIsco3: (o.attrs.parentIsco3 as string) ?? isco.slice(0, 3),
      escoOccupationCount: (o.attrs.escoOccupationCount as number) ?? 0,
      competencies, routes,
    };
  }).sort((a, b) => a.nameRu.localeCompare(b.nameRu, 'ru'));

  const bySlug = new Map(professions.map((p) => [p.slug, p]));
  const byDirectionOkso = new Map<string, { slug: string; nameRu: string; confidence: number }[]>();
  for (const p of professions) {
    for (const r of p.routes) {
      const arr = byDirectionOkso.get(r.okso) ?? [];
      arr.push({ slug: p.slug, nameRu: p.nameRu, confidence: r.confidence });
      byDirectionOkso.set(r.okso, arr);
    }
  }
  for (const arr of byDirectionOkso.values()) arr.sort((a, b) => b.confidence - a.confidence);
  cache = { professions, bySlug, byDirectionOkso };
  return cache;
}
