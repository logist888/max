// Ингест профессий и компетенций из подготовленных интермедиатов
// (data/graph/prepared/*, собраны graph_prep.py из ISCO-08 + ОКЗ + ESCO).
// Профессия = группа ISCO-08 (4 знака): en-метка из ISCO, ru-метка из ОКЗ.
// Компетенции — навыки ESCO; связь REQUIRES — авторитетная (ESCO).

import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import type { Staged } from './index.ts';
import { SRC, edge, escoSkillKey, node, prov } from './helpers.ts';

interface PrepOcc {
  isco4: string; titleEn: string; definitionEn: string; tasksEn: string;
  labelRu: string | null; escoOccupationCount: number; escoLabelsEn: string[];
  okzExamples: string[]; parent3: string;
}
interface PrepComp { uri: string; labelEn: string; skillType: string; }
interface PrepOC { isco4: string; skill: string; kind: 'essential' | 'optional'; weight: number; }

export function ingestOccupations(ctx: { appDir: string }): Staged {
  const dir = resolve(ctx.appDir, '../data/graph/prepared');
  const load = <T>(f: string): T => JSON.parse(readFileSync(join(dir, f), 'utf8')) as T;
  const occ = load<PrepOcc[]>('occupations.json');
  const comp = load<PrepComp[]>('competencies.json');
  const oc = load<PrepOC[]>('occupation_competency.json');

  const nodes = [];
  const edges = [];

  for (const o of occ) {
    const labels: Record<string, string> = { en: o.titleEn };
    if (o.labelRu) labels.ru = o.labelRu;
    // Профессия — факт (ISCO + ОКЗ авторитетны). Без русской метки — требует-проверки.
    nodes.push(node({
      type: 'Occupation', key: o.isco4,
      localIds: [{ scheme: 'isco08', value: o.isco4 }],
      labels,
      status: o.labelRu ? 'факт' : 'требует-проверки',
      confidence: o.labelRu ? 0.95 : 0.7,
      provenance: [prov(SRC.isco, o.isco4), ...(o.labelRu ? [prov(SRC.okz, o.isco4)] : [])],
      attrs: {
        definitionEn: o.definitionEn, tasksEn: o.tasksEn,
        escoOccupationCount: o.escoOccupationCount, escoLabelsEn: o.escoLabelsEn,
        okzExamples: o.okzExamples,
        parentIsco3: o.parent3,
      },
    }));
  }

  for (const c of comp) {
    nodes.push(node({
      type: 'Competency', key: escoSkillKey(c.uri),
      localIds: [{ scheme: 'esco', value: c.uri }],
      labels: { en: c.labelEn },
      status: 'факт',
      confidence: 0.95,
      provenance: [prov(SRC.esco, c.uri)],
      attrs: { skillType: c.skillType },
    }));
  }

  for (const r of oc) {
    const from = `me:occupation:${r.isco4}`;
    const to = `me:competency:${escoSkillKey(r.skill)}`;
    edges.push(edge({
      type: 'REQUIRES', from, to,
      weight: r.weight, confidence: 0.9,
      method: 'authoritative', status: 'факт',
      provenance: [prov(SRC.esco, r.skill)],
      explanation: r.kind === 'essential'
        ? `Ключевая компетенция профессии по ESCO (essential для ${Math.round(r.weight * 100)}% профессий группы).`
        : `Дополнительная компетенция профессии по ESCO.`,
    }));
  }

  return {
    nodes, edges,
    sources: [
      { source: 'ISCO-08 + ОКЗ (профессии)', records: occ.length },
      { source: 'ESCO v1.2.1 (компетенции)', records: comp.length },
      { source: 'ESCO occupation→skill', records: oc.length },
    ],
  };
}
