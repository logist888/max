/**
 * Разрешение связей сущности для инспектора: родители, потомки, правила, решения.
 * Работает поверх доменного графа — не знает о конкретных кодах.
 */

import type { CellStatus, Decision, ID, Inspectable, Rule } from '@/types';
import type { DomainGraph, GraphNode, ResolvedRelation } from '@/types/graph';
import { DECISIONS, RULES } from '@/data';

const ACTION_TO_STATUS: Partial<Record<Decision['action'], CellStatus>> = {
  scale: 'scaling',
  stop: 'stopped',
  pause: 'paused',
};

export function buildNodeIndex(domain: DomainGraph): ReadonlyMap<ID, GraphNode> {
  return new Map(domain.nodes.map((n) => [n.id, n]));
}

/** Входящие и исходящие связи узла (для панелей «родители/потомки»). */
export function getRelations(
  domain: DomainGraph,
  nodeId: ID,
  index: ReadonlyMap<ID, GraphNode>,
): { incoming: ResolvedRelation[]; outgoing: ResolvedRelation[] } {
  const incoming: ResolvedRelation[] = [];
  const outgoing: ResolvedRelation[] = [];
  for (const edge of domain.edges) {
    if (edge.source === nodeId) {
      const node = index.get(edge.target);
      if (node) outgoing.push({ edge, node, direction: 'outgoing' });
    } else if (edge.target === nodeId) {
      const node = index.get(edge.source);
      if (node) incoming.push({ edge, node, direction: 'incoming' });
    }
  }
  return { incoming, outgoing };
}

/** Правила, в которых участвует узел (как источник или как посадочная). */
export function getRelatedRules(nodeId: ID): Rule[] {
  return RULES.filter(
    (r) =>
      r.sourceIds.includes(nodeId) ||
      r.primaryLandingId === nodeId ||
      r.allowedLandingIds.includes(nodeId) ||
      r.forbidden.some((f) => f.landingId === nodeId),
  );
}

/** Решения, относящиеся к сущности (метрика → её решения; ячейка → решения по её статусу). */
export function getRelatedDecisions(entity: Inspectable): Decision[] {
  switch (entity.kind) {
    case 'metric':
      return DECISIONS.filter((d) => d.metricId === entity.id);
    case 'decision':
      return DECISIONS.filter((d) => d.id === entity.id);
    case 'cell':
      return DECISIONS.filter((d) => ACTION_TO_STATUS[d.action] === entity.status);
    default:
      return [];
  }
}
