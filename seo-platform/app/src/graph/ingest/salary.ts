// Ингест зарплат (легальные госисточники) из подготовленного salary.json
// (собран graph_salary.py: Росстат по проф. группам ОКЗ + медиана по вакансиям
// «Работа России»). Узел Salary на занятие + ребро HAS_SALARY (Occupation→Salary).
// hh.ru не используется — запрещён его соглашением (licenses: hh-api=blocked).

import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import type { Staged } from './index.ts';
import { SRC, edge, node, prov } from './helpers.ts';

interface RosstatFig { avg: number; currency: string; date: string; level?: string; }
interface TrudvsemFig { median: number; p25: number; p75: number; count: number; currency: string; retrievedAt: string; }
type SalaryRec = { rosstat?: RosstatFig; trudvsem?: TrudvsemFig };

export function ingestSalary(ctx: { appDir: string }): Staged {
  const path = resolve(ctx.appDir, '../data/graph/prepared/salary.json');
  let data: Record<string, SalaryRec> = {};
  try { data = JSON.parse(readFileSync(path, 'utf8')) as Record<string, SalaryRec>; } catch { data = {}; }

  const nodes = [];
  const edges = [];
  for (const [isco, rec] of Object.entries(data)) {
    if (!rec.rosstat && !rec.trudvsem) continue;
    const provenance = [];
    if (rec.rosstat) provenance.push(prov(SRC.rosstat, isco));
    if (rec.trudvsem) provenance.push(prov(SRC.trudvsem, isco));
    const key = `${isco}`;
    nodes.push(node({
      type: 'Salary', key,
      localIds: [{ scheme: 'isco08', value: isco }],
      labels: { ru: `Зарплата — ${isco}` },
      status: 'факт', confidence: 0.9,
      provenance,
      attrs: {
        currency: 'RUB',
        rosstatAvg: rec.rosstat?.avg ?? null,
        rosstatDate: rec.rosstat?.date ?? null,
        rosstatLevel: rec.rosstat?.level ?? null,
        trudvsemMedian: rec.trudvsem?.median ?? null,
        trudvsemP25: rec.trudvsem?.p25 ?? null,
        trudvsemP75: rec.trudvsem?.p75 ?? null,
        trudvsemCount: rec.trudvsem?.count ?? null,
        trudvsemDate: rec.trudvsem?.retrievedAt ?? null,
      },
    }));
    const parts = [];
    if (rec.rosstat) parts.push(`средняя по Росстату ${rec.rosstat.avg.toLocaleString('ru-RU')} ₽ (${rec.rosstat.date})`);
    if (rec.trudvsem) parts.push(`медиана по вакансиям ${rec.trudvsem.median.toLocaleString('ru-RU')} ₽ (Работа России, ${rec.trudvsem.count} вак.)`);
    edges.push(edge({
      type: 'HAS_SALARY',
      from: `me:occupation:${isco}`,
      to: `me:salary:${key}`,
      weight: null, confidence: 0.9, method: 'authoritative', status: 'факт',
      provenance,
      explanation: `Зарплата: ${parts.join('; ')}. Источники государственные, открытые.`,
    }));
  }
  return { nodes, edges, sources: nodes.length ? [{ source: 'Зарплаты (Росстат + Работа России)', records: nodes.length }] : [] };
}
