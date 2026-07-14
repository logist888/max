/**
 * Детерминированная слоистая (swimlane) раскладка.
 *
 * Каждый узел получает вертикальную полосу по layer.order; горизонтальный порядок внутри
 * полосы уточняется барицентром соседей (уменьшение пересечений). Координаты не задаются
 * вручную — раскладка полностью выводится из данных и перестраивается при их изменении.
 */

import type { GraphNode, NodeSize, Positioned, RelationType } from '@/types/graph';
import type { LayerId } from '@/types';
import { LAYERS } from '@/data';
import { LAYOUT, NODE_SIZES } from '@/constants/config';

export interface ComposedNode extends GraphNode {
  readonly dimmed: boolean;
  readonly collapsed: boolean;
}

export interface OrderingEdge {
  readonly source: string;
  readonly target: string;
  readonly type: RelationType;
}

export interface LaidOutNode extends ComposedNode {
  readonly position: Positioned;
  readonly size: NodeSize;
}

const LAYER_ORDER: ReadonlyMap<LayerId, number> = new Map(LAYERS.map((l) => [l.id, l.order]));

function sizeOf(node: GraphNode): NodeSize {
  return NODE_SIZES[node.kind];
}

/**
 * @param sortKey исходный порядок узла (для стабильной начальной сортировки внутри полосы).
 */
export function layoutLayered(
  nodes: readonly ComposedNode[],
  edges: readonly OrderingEdge[],
  sortKey: ReadonlyMap<string, number>,
): LaidOutNode[] {
  if (nodes.length === 0) return [];

  // 1. Группировка по полосам (layer.order), пустые полосы отбрасываются, порядок сохраняется.
  const byBand = new Map<number, ComposedNode[]>();
  for (const node of nodes) {
    const band = LAYER_ORDER.get(node.layer) ?? 0;
    const bucket = byBand.get(band) ?? [];
    bucket.push(node);
    byBand.set(band, bucket);
  }
  const bandKeys = [...byBand.keys()].sort((a, b) => a - b);
  const bands: ComposedNode[][] = bandKeys.map((k) =>
    [...byBand.get(k)!].sort((a, b) => (sortKey.get(a.id) ?? 0) - (sortKey.get(b.id) ?? 0)),
  );

  // 2. Уменьшение пересечений барицентром: чередуем проходы вниз/вверх.
  const neighbors = buildAdjacency(edges);
  for (let pass = 0; pass < LAYOUT.orderingPasses; pass += 1) {
    const downward = pass % 2 === 0;
    const range = downward
      ? [...bands.keys()].slice(1)
      : [...bands.keys()].slice(0, -1).reverse();
    for (const bi of range) {
      const fixedBand = bands[downward ? bi - 1 : bi + 1];
      const posInFixed = new Map(fixedBand.map((n, i) => [n.id, i]));
      bands[bi] = stableSortByBarycenter(bands[bi], neighbors, posInFixed);
    }
  }

  // 3. Назначение координат: y по полосам, x — центрирование внутри полосы.
  const result: LaidOutNode[] = [];
  let cursorY = 0;
  for (const band of bands) {
    const sizes = band.map(sizeOf);
    const bandHeight = Math.max(...sizes.map((s) => s.height));
    const totalWidth =
      sizes.reduce((sum, s) => sum + s.width, 0) + LAYOUT.nodeGap * (band.length - 1);
    let cursorX = -totalWidth / 2;
    band.forEach((node, i) => {
      const size = sizes[i];
      result.push({
        ...node,
        size,
        position: { x: cursorX, y: cursorY + (bandHeight - size.height) / 2 },
      });
      cursorX += size.width + LAYOUT.nodeGap;
    });
    cursorY += bandHeight + LAYOUT.bandGap;
  }
  return result;
}

function buildAdjacency(edges: readonly OrderingEdge[]): Map<string, string[]> {
  const adj = new Map<string, string[]>();
  const add = (a: string, b: string) => {
    const list = adj.get(a) ?? [];
    list.push(b);
    adj.set(a, list);
  };
  for (const e of edges) {
    add(e.source, e.target);
    add(e.target, e.source);
  }
  return adj;
}

function stableSortByBarycenter(
  band: readonly ComposedNode[],
  neighbors: ReadonlyMap<string, string[]>,
  posInFixed: ReadonlyMap<string, number>,
): ComposedNode[] {
  const withKey = band.map((node, i) => {
    const ns = (neighbors.get(node.id) ?? []).map((id) => posInFixed.get(id)).filter(
      (v): v is number => v !== undefined,
    );
    const bary = ns.length ? ns.reduce((a, b) => a + b, 0) / ns.length : Number.NaN;
    return { node, bary, i };
  });
  // Узлы без связей в соседней полосе сохраняют исходное относительное положение.
  return withKey
    .map((w) => (Number.isNaN(w.bary) ? { ...w, bary: w.i } : w))
    .sort((a, b) => a.bary - b.bary || a.i - b.i)
    .map((w) => w.node);
}
