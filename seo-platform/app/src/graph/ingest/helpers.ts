// Конструкторы узлов/связей с провенансом и детерминированными id.
// Пресеты лицензий — коды из config/graph/licenses.json.

import type { EdgeType, GraphEdge, GraphNode, LocalId, Method, NodeType, Provenance, Status } from '../types.ts';

const VALID_AS_OF = '2026-07-13';

export const SRC = {
  isco: { source: 'ISCO-08 (ILO)', license: 'isco-08', method: 'authoritative' as Method, sourceUrl: 'https://ilostat.ilo.org' },
  okz: { source: 'ОКЗ ОК 010-2014 (МСКЗ-08)', license: 'okz-2014', method: 'authoritative' as Method },
  esco: { source: 'ESCO v1.2.1', license: 'esco-1.2.1', method: 'authoritative' as Method, sourceUrl: 'https://esco.ec.europa.eu' },
  edu: { source: 'ВУЗ-навигатор, Госуслуги', license: 'edu-snapshot', method: 'authoritative' as Method },
  ugs: { source: 'Минобрнауки России, Перечень УГСН', license: 'minobr-ugs', method: 'authoritative' as Method },
  curated: { source: 'Экспертное курирование MainExperts', license: 'internal-curated', method: 'curated' as Method },
  rosstat: { source: 'Росстат (обследование по проф. группам ОКЗ)', license: 'rosstat', method: 'authoritative' as Method, sourceUrl: 'https://rosstat.gov.ru/labour_costs' },
  trudvsem: { source: 'Работа России (trudvsem.ru)', license: 'trudvsem', method: 'authoritative' as Method, sourceUrl: 'https://trudvsem.ru' },
} as const;

export function prov(preset: { source: string; license: string; method: Method; sourceUrl?: string }, sourceId?: string): Provenance {
  return { source: preset.source, license: preset.license, method: preset.method, sourceUrl: preset.sourceUrl, sourceId, sourceDate: '2024-2026' };
}

export function node(opts: {
  type: NodeType; key: string; localIds: LocalId[];
  labels: GraphNode['labels']; status: Status; confidence: number;
  provenance: Provenance[]; attrs?: Record<string, unknown>;
}): GraphNode {
  return {
    id: `me:${opts.type.toLowerCase()}:${opts.key}`,
    type: opts.type,
    localIds: opts.localIds,
    labels: opts.labels,
    status: opts.status,
    confidence: opts.confidence,
    validAsOf: VALID_AS_OF,
    provenance: opts.provenance,
    version: 1,
    attrs: opts.attrs ?? {},
  };
}

export function edge(opts: {
  type: EdgeType; from: string; to: string;
  weight?: number | null; probability?: number | null; confidence: number;
  method: Method; status: Status; provenance: Provenance[]; explanation: string;
}): GraphEdge {
  return {
    id: `me:edge:${opts.from}--${opts.type}--${opts.to}`,
    type: opts.type,
    from: opts.from,
    to: opts.to,
    direction: 'directed',
    weight: opts.weight ?? null,
    probability: opts.probability ?? null,
    confidence: opts.confidence,
    method: opts.method,
    status: opts.status,
    provenance: opts.provenance,
    explanation: opts.explanation,
    validAsOf: VALID_AS_OF,
    createdAt: VALID_AS_OF,
  };
}

/** Хвост ESCO-URI навыка → компактный ключ узла компетенции. */
export function escoSkillKey(uri: string): string {
  return 'esco-' + uri.split('/').pop();
}
