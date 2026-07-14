/**
 * Построение доменного графа из словарей data/*.
 *
 * Компоненты НЕ знают о конкретных MK/PG/CELL — они получают уже собранные узлы и рёбра.
 * Добавление сущности в data/* автоматически появляется в графе: здесь нет ни одного
 * захардкоженного объекта, только обход моделей и их связей.
 */

import type { CellStatus, DomainEntity, ID } from '@/types';
import type { DomainGraph, GraphEdge, GraphNode, RelationType } from '@/types/graph';
import {
  ALL_ENTITIES,
  ANALYTICS_NODES,
  CELLS,
  CONTRACTORS,
  DECISIONS,
  FLOW_STEPS,
  LANDINGS,
  RULES,
} from '@/data';

/** Действие решения → статус ячейки, на который оно воздействует. */
const ACTION_TO_STATUS: Partial<Record<string, CellStatus>> = {
  scale: 'scaling',
  stop: 'stopped',
  pause: 'paused',
};

function toNode(entity: DomainEntity): GraphNode {
  return { id: entity.id, kind: entity.kind, layer: entity.layer, entity };
}

function edge(
  source: ID,
  target: ID,
  type: RelationType,
  extra?: Pick<GraphEdge, 'label' | 'reason' | 'hypothesis'>,
): GraphEdge {
  return { id: `${type}:${source}->${target}`, source, target, type, ...extra };
}

/** Собирает полный доменный граф (все узлы и все рёбра, без раскладки). */
export function buildDomainGraph(): DomainGraph {
  const nodes: GraphNode[] = ALL_ENTITIES.map(toNode);
  const nodeIds = new Set(nodes.map((n) => n.id));
  const rawEdges: GraphEdge[] = [];

  // 1. Правила связей: источник → посадочная (осн./допустимая/запрещённая).
  for (const rule of RULES) {
    for (const src of rule.sourceIds) {
      rawEdges.push(edge(src, rule.primaryLandingId, 'traffic_to_landing', { label: rule.code }));
      for (const allowed of rule.allowedLandingIds) {
        rawEdges.push(edge(src, allowed, 'allowed_landing'));
      }
      for (const f of rule.forbidden) {
        rawEdges.push(edge(src, f.landingId, 'forbidden', { reason: f.reason }));
      }
    }
  }

  // 2. Посадочная → целевое событие.
  for (const landing of LANDINGS) {
    rawEdges.push(edge(landing.id, landing.targetEventId, 'landing_to_event'));
  }

  // 3. Пользовательский поток: основная цепочка + вне-линейные события.
  const chain = FLOW_STEPS.filter((s) => s.mainChain).sort((a, b) => a.order - b.order);
  for (let i = 0; i < chain.length - 1; i += 1) {
    rawEdges.push(edge(chain[i].id, chain[i + 1].id, 'flow_next'));
  }
  for (const step of FLOW_STEPS) {
    for (const target of step.feedsInto ?? []) {
      rawEdges.push(edge(step.id, target, 'flow_next'));
    }
    // 4. Платформа → аналитический контур.
    for (const target of step.emitsTo ?? []) {
      rawEdges.push(edge(step.id, target, 'emits_data', { label: step.eventCode }));
    }
  }

  // 5. Аналитический контур: цепочка узлов + мост к слою метрик.
  const contour = [...ANALYTICS_NODES].sort((a, b) => a.order - b.order);
  for (let i = 0; i < contour.length - 1; i += 1) {
    rawEdges.push(edge(contour[i].id, contour[i + 1].id, 'analytics_flow', { label: contour[i].flowLabel }));
  }
  for (const node of ANALYTICS_NODES) {
    for (const metricId of node.feedsInto ?? []) {
      rawEdges.push(edge(node.id, metricId, 'analytics_flow', { label: 'оценка канала' }));
    }
  }

  // 6. Метрика → решение.
  for (const decision of DECISIONS) {
    rawEdges.push(edge(decision.metricId, decision.id, 'metric_to_decision', { hypothesis: decision.hypothesis }));
  }

  // 7. Решение → ячейка (по результирующему статусу).
  for (const decision of DECISIONS) {
    const status = ACTION_TO_STATUS[decision.action];
    if (!status) continue;
    for (const cell of CELLS) {
      if (cell.status === status) {
        rawEdges.push(edge(decision.id, cell.id, 'decision_to_target', { label: decision.actionLabel }));
      }
    }
  }

  // 8. Ячейка → её канал и посадочная; управление по ДРР.
  for (const cell of CELLS) {
    rawEdges.push(edge(cell.id, cell.channelId, 'cell_uses_channel'));
    rawEdges.push(edge(cell.id, cell.landingId, 'cell_uses_landing'));
    if (cell.status !== 'draft') {
      rawEdges.push(edge(cell.id, 'metric_drr', 'cell_governed_by', { label: 'ДРР' }));
    }
  }

  // 9. ТЗ подрядчику → ячейка, для которой заполнен пример.
  for (const contractor of CONTRACTORS) {
    const example = contractor.fields.find((f) => f.key === 'cell')?.value;
    const target = CELLS.find((c) => c.code === example);
    if (target) rawEdges.push(edge(contractor.id, target.id, 'contractor_instantiates'));
  }

  return { nodes, edges: dedupeEdges(rawEdges, nodeIds) };
}

/**
 * Убирает дубли и применяет приоритет запрета: если между парой (источник→посадочная)
 * есть forbidden, прочие рёбра этой пары скрываются (сильнейшее ограничение — на карте).
 */
function dedupeEdges(edges: readonly GraphEdge[], nodeIds: ReadonlySet<ID>): GraphEdge[] {
  const forbiddenPairs = new Set<string>();
  for (const e of edges) {
    if (e.type === 'forbidden') forbiddenPairs.add(`${e.source}->${e.target}`);
  }

  const seen = new Set<string>();
  const out: GraphEdge[] = [];
  for (const e of edges) {
    if (!nodeIds.has(e.source) || !nodeIds.has(e.target)) continue;
    if (e.source === e.target) continue;
    const pair = `${e.source}->${e.target}`;
    if (e.type !== 'forbidden' && forbiddenPairs.has(pair)) continue;
    if (seen.has(e.id)) continue;
    seen.add(e.id);
    out.push(e);
  }
  return out;
}
