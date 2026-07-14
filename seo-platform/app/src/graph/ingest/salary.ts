// Ингест зарплат из подготовленного salary.json (собран graph_salary.py на базе
// Росстата: средняя по проф. группам ОКЗ, окт-2023, индексирована к текущему уровню
// РФ и с коэффициентом Москвы). Узел Salary на занятие + ребро HAS_SALARY.
//
// База — авторитетный Росстат; avgRF/avgMoscow — ПОМЕЧЕННАЯ ОЦЕНКА (индексация и
// коэф. Москвы единые для всех групп). hh.ru и «Работа России» не используются
// (licenses: hh-api=blocked; trudvsem — unused, системно занижает).

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import type { Provenance } from '../types.ts';
import type { Staged } from './index.ts';
import { SRC, edge, node } from './helpers.ts';

interface RosstatFig {
  avgBase: number; baseDate: string; avgRF: number; avgMoscow: number;
  indexedTo: string; indexFactor: number; moscowCoef: number;
  matchLevel: string; matchCode: string; currency: string;
  source: string; retrievedAt: string;
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
    // Провенанс: авторитетный Росстат, дата базы = период обследования.
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
        avgBase: r.avgBase, baseDate: r.baseDate,
        avgRF: r.avgRF, avgMoscow: r.avgMoscow,
        indexedTo: r.indexedTo, indexFactor: r.indexFactor, moscowCoef: r.moscowCoef,
        matchLevel: r.matchLevel,
        // Явная пометка: avgRF/avgMoscow — оценка, не точный факт по группе.
        estimate: true,
      },
    }));
    edges.push(edge({
      type: 'HAS_SALARY',
      from: `me:occupation:${isco}`,
      to: `me:salary:${key}`,
      weight: null, confidence: 0.8, method: 'authoritative', status: 'факт',
      provenance,
      explanation: `Оценка зарплаты: база Росстат (${r.matchLevel}, ${r.baseDate}) `
        + `${rub(r.avgBase)} ₽ × индекс ${r.indexFactor} → по РФ ~${rub(r.avgRF)} ₽/мес; `
        + `Москва ×${r.moscowCoef} → ~${rub(r.avgMoscow)} ₽/мес (${r.indexedTo}). `
        + `Коэффициенты единые для всех групп — это помеченная оценка, не точный факт.`,
    }));
  }
  return { nodes, edges, sources: nodes.length ? [{ source: 'Зарплаты (Росстат, индексировано)', records: nodes.length }] : [] };
}
