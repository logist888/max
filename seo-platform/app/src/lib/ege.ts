// Доступ к маппингу «направление → предметы ЕГЭ» (перечень вступительных испытаний
// Минобрнауки, приказ № 820). Источник — data/ege/ege-subjects.json (собран
// scripts/build_ege_map.py). Джойн с направлениями витрины db().directions.
//
// Уровень направления, не вуза: конкретный набор ЕГЭ определяют правила приёма вуза.
// Русский язык обязателен везде и как различающий предмет не выносится.

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { db } from './data.ts';

export interface EgeSubject { key: string; slug: string; nom: string; instr: string; }
// 7 различающих предметов с реальным спросом (русский/математика — почти универсальны,
// отдельными страницами не делаем).
export const EGE_SUBJECTS: EgeSubject[] = [
  { key: 'обществознание', slug: 'obshchestvoznaniem', nom: 'обществознание', instr: 'обществознанием' },
  { key: 'биология',       slug: 'biologiej',          nom: 'биология',       instr: 'биологией' },
  { key: 'химия',          slug: 'himiej',             nom: 'химия',          instr: 'химией' },
  { key: 'история',        slug: 'istoriej',           nom: 'история',        instr: 'историей' },
  { key: 'информатика',    slug: 'informatikoj',       nom: 'информатика',    instr: 'информатикой' },
  { key: 'физика',         slug: 'fizikoj',            nom: 'физика',         instr: 'физикой' },
  { key: 'география',       slug: 'geografiej',         nom: 'география',       instr: 'географией' },
];

export interface EgeDir { slug: string; name: string; level: string; ugsCode: string; ugsName: string; okso: string; }

interface Cache {
  meta: { source: string; sourceUrl: string; note: string };
  bySubject: Map<string, EgeDir[]>;   // subject.key → направления (бак/спец), дедуп по slug
  byOkso: Map<string, string[]>;      // ОКСО(6) → предметы (для блока на /specialnost/)
  bySlug: Map<string, string[]>;      // slug направления → предметы
}
let cache: Cache | null = null;

const okso6 = (okso: string) => okso.replace(/^\d+\./, '');

export function ege(): Cache {
  if (cache) return cache;
  const raw = JSON.parse(
    readFileSync(resolve(process.cwd(), '../data/ege/ege-subjects.json'), 'utf8'),
  ) as { meta: Cache['meta']; subjects: Record<string, string[]> };

  const { directions, ugs } = db();
  const ugsName = new Map(ugs.map((g: { code: string; name?: string }) => [g.code, g.name ?? `Группа ${g.code}`]));

  const bySubject = new Map<string, EgeDir[]>();
  for (const s of EGE_SUBJECTS) bySubject.set(s.key, []);
  const byOkso = new Map<string, string[]>();
  const bySlug = new Map<string, string[]>();
  const seen = new Map<string, Set<string>>(); // subject → set(slug) для дедупа

  for (const d of directions) {
    if (d.level !== 'Бакалавриат' && d.level !== 'Специалитет') continue;
    const code = okso6(d.okso);
    const subs = raw.subjects[code];
    if (!subs) continue;
    byOkso.set(code, subs);
    bySlug.set(d.slug, subs);
    for (const sub of subs) {
      const bucket = bySubject.get(sub);
      if (!bucket) continue; // не различающий (русский/математика/…)
      const seenSet = seen.get(sub) ?? seen.set(sub, new Set()).get(sub)!;
      if (seenSet.has(d.slug)) continue;
      seenSet.add(d.slug);
      bucket.push({
        slug: d.slug, name: d.name, level: d.level,
        ugsCode: d.ugsCode, ugsName: ugsName.get(d.ugsCode) ?? `Группа ${d.ugsCode}`, okso: code,
      });
    }
  }
  for (const arr of bySubject.values()) {
    arr.sort((a, b) => a.ugsCode.localeCompare(b.ugsCode) || a.name.localeCompare(b.name, 'ru'));
  }
  cache = { meta: raw.meta, bySubject, byOkso, bySlug };
  return cache;
}
