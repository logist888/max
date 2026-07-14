/**
 * Композиция представления: сворачивание слоёв в агрегаты, агрегация межслойных рёбер,
 * приглушение по фильтрам и запуск раскладки. Результат — то, что рисует Canvas.
 */

import type { DomainGraph, GraphEdge, GraphNode, RelationType, ViewEdge, ViewGraph } from '@/types/graph';
import type { LayerId } from '@/types';
import { CONTEXTUAL_RELATIONS } from '@/constants/config';
import { ALL_ENTITIES, LAYERS } from '@/data';
import { layoutLayered, type ComposedNode, type OrderingEdge } from './layout';

export interface ComposeOptions {
  readonly expandedLayers: ReadonlySet<LayerId>;
  /** true → узел совпадает с активными фильтрами (не приглушается). */
  readonly matches: (node: GraphNode) => boolean;
  readonly filtersActive: boolean;
}

const SORT_KEY: ReadonlyMap<string, number> = new Map(
  ALL_ENTITIES.map((e, i) => [e.id, i]),
);

function summaryId(layer: LayerId): string {
  return `layer:${layer}`;
}

export function composeView(domain: DomainGraph, opts: ComposeOptions): ViewGraph {
  const { expandedLayers, matches, filtersActive } = opts;
  const layerOfNode = new Map(domain.nodes.map((n) => [n.id, n.layer]));

  // — Узлы —
  const composed: ComposedNode[] = [];
  const countByLayer = new Map<LayerId, number>();
  for (const n of domain.nodes) countByLayer.set(n.layer, (countByLayer.get(n.layer) ?? 0) + 1);

  for (const layer of LAYERS) {
    if (expandedLayers.has(layer.id)) {
      for (const n of domain.nodes) {
        if (n.layer !== layer.id) continue;
        composed.push({ ...n, dimmed: filtersActive && !matches(n), collapsed: false });
      }
    } else if ((countByLayer.get(layer.id) ?? 0) > 0) {
      composed.push({
        id: summaryId(layer.id),
        kind: 'layer_group',
        layer: layer.id,
        memberCount: countByLayer.get(layer.id) ?? 0,
        dimmed: false,
        collapsed: true,
      });
    }
  }
  const visibleIds = new Set(composed.map((n) => n.id));

  // — Рёбра: разрешение концов + агрегация —
  const resolve = (id: string): { id: string; collapsed: boolean } => {
    const layer = layerOfNode.get(id);
    if (layer && !expandedLayers.has(layer)) return { id: summaryId(layer), collapsed: true };
    return { id, collapsed: false };
  };

  const acc = new Map<string, ViewEdge & { _count: number }>();
  for (const e of domain.edges) {
    const s = resolve(e.source);
    const t = resolve(e.target);
    if (s.id === t.id) continue;
    if (!visibleIds.has(s.id) || !visibleIds.has(t.id)) continue;

    const aggregated = s.collapsed || t.collapsed;
    const isForbidden = e.type === 'forbidden';
    const isContextual = CONTEXTUAL_RELATIONS.has(e.type);
    // Запреты и контекстные связи не агрегируем — только при раскрытых слоях.
    if (aggregated && (isForbidden || isContextual)) continue;

    const type: RelationType = aggregated ? 'layer_flow' : e.type;
    const key = `${s.id}->${t.id}->${type}`;
    const existing = acc.get(key);
    if (existing) {
      existing._count += 1;
    } else {
      acc.set(key, {
        id: key,
        source: s.id,
        target: t.id,
        type,
        label: aggregated ? undefined : e.label,
        reason: aggregated ? undefined : e.reason,
        hypothesis: e.hypothesis,
        contextual: !aggregated && isContextual,
        count: 1,
        _count: 1,
      });
    }
  }
  const edges: ViewEdge[] = [...acc.values()].map(({ _count, ...rest }) => ({ ...rest, count: _count }));

  // — Раскладка: только структурные (не контекстные) рёбра влияют на порядок —
  const orderingEdges: OrderingEdge[] = edges
    .filter((e) => !e.contextual)
    .map((e) => ({ source: e.source, target: e.target, type: e.type }));

  const laidOut = layoutLayered(composed, orderingEdges, SORT_KEY);
  return { nodes: laidOut, edges };
}

/** Доменные рёбра, инцидентные узлу (для инспектора и подсветки). */
export function incidentDomainEdges(domain: DomainGraph, nodeId: string): GraphEdge[] {
  return domain.edges.filter((e) => e.source === nodeId || e.target === nodeId);
}
