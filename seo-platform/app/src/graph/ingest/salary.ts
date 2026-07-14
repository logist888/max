// Ингест зарплат из подготовленного salary.json (собран graph_salary.py на базе
// Росстата: обследование ЗП по группам занятий ОКЗ, ОКТЯБРЬ 2025). Узел Salary на
// занятие + ребро HAS_SALARY.
//
// avgRF — средняя по группе занятий на самом детальном уровне (3→2→1 знак ОКЗ), 2025.
// avgMoscow — avgRF × фактическая надбавка Москва/РФ по майор-группе (лист 31 Росстата),
// не плоский коэффициент. Это ПОМЕЧЕННАЯ ОЦЕНКА по группе, не факт по конкретной должности.
// hh.ru и «Работа России» не используются (licenses: hh-api=blocked; trudvsem — unused).

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import type { Provenance } from '../types.ts';
import type { Staged } from './index.ts';
import { SRC, edge, node } from './helpers.ts';

interface RosstatFig {
  avgRF: number; avgMoscow: number | null; baseDate: string;
  matchLevel: string; matchCode: string;
  moscowRatio: number | null; moscowMajor: string;
  currency: string; source: string; retrievedAt: string;
}
type SalaryRec = { rosstat?: RosstatFig };

const rub = (n: number) => n.toLocaleString('ru-RU');

export function ingestSalary(ctx: { appDir: string }): Staged {
  const path = resolve(ctx.appDir, '../data/graph/prepared/salary.json');
  let data: Record<string, SalaryRec> = {};
  try { data = JSON.parse(readFileSync(path, 'utf8')) as Record<string, SalaryRec>; } catch { data = {}; }

  const nodes = [];
  const edges = [];
  for (const [isco, rec] of Object.entries(data)) {
    const r = rec.rosstat;
    if (!r) continue;
    // Провенанс: авторитетный Росстат, дата = период обследования (окт-2025).
    const provenance: Provenance[] = [{
      source: SRC.rosstat.source, license: SRC.rosstat.license, method: SRC.rosstat.method,
      sourceUrl: SRC.rosstat.sourceUrl, sourceId: r.matchCode, sourceDate: r.baseDate,
      retrievedAt: r.retrievedAt,
    }];
    const key = `${isco}`;
    nodes.push(node({
      type: 'Salary', key,
      localIds: [{ scheme: 'okz', value: isco }],
      labels: { ru: `Зарплата — ${isco}` },
      status: 'факт', confidence: 0.8,
      provenance,
      attrs: {
        currency: 'RUB',
        avgRF: r.avgRF, avgMoscow: r.avgMoscow, baseDate: r.baseDate,
        matchLevel: r.matchLevel, moscowRatio: r.moscowRatio,
        // Явная пометка: это оценка по группе занятий, не точный факт по должности.
        estimate: true,
      },
    }));
    const mos = r.avgMoscow ? `; Москва ~${rub(r.avgMoscow)} ₽/мес (надбавка ×${r.moscowRatio})` : '';
    edges.push(edge({
      type: 'HAS_SALARY',
      from: `me:occupation:${isco}`,
      to: `me:salary:${key}`,
      weight: null, confidence: 0.8, method: 'authoritative', status: 'факт',
      provenance,
      explanation: `Средняя ЗП по группе занятий (${r.matchLevel}), Росстат ${r.baseDate}: `
        + `по РФ ~${rub(r.avgRF)} ₽/мес${mos}. Оценка по группе, не гарантированный доход по должности.`,
    }));
  }
  return { nodes, edges, sources: nodes.length ? [{ source: 'Зарплаты (Росстат, окт-2025)', records: nodes.length }] : [] };
}
