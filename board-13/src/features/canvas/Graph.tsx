import { useEffect, useMemo } from 'react';
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  MarkerType,
  useReactFlow,
  type Edge,
  type Node,
} from '@xyflow/react';
import type { LayerId } from '@/types';
import type { ViewEdge, ViewGraph, ViewNode } from '@/types/graph';
import { NEIGHBORS } from '@/app/graph';
import { useActions, useAppState } from '@/app/store';
import { LAYER_COLORS, RELATION_STYLES } from '@/data/colors';
import { CONTEXTUAL_RELATIONS, FORBIDDEN_RELATIONS, SECONDARY_RELATIONS } from '@/constants/config';
import { nodeTypes } from '@/components/nodes/nodeTypes';
import { edgeTypes } from '@/components/edges/FlowConnector';

const defaultEdgeOptions = { type: 'flow' };

function rfNodeType(node: ViewNode): string {
  if (node.kind === 'layer_group') return 'layer';
  if (node.kind === 'cell') return 'cell';
  if (node.kind === 'contractor') return 'contractor';
  return 'entity';
}

function edgeVisible(
  e: ViewEdge,
  selectedId: string | null,
  showSecondary: boolean,
  showForbidden: boolean,
): boolean {
  if (e.contextual || CONTEXTUAL_RELATIONS.has(e.type)) {
    return selectedId !== null && (e.source === selectedId || e.target === selectedId);
  }
  if (FORBIDDEN_RELATIONS.has(e.type)) return showForbidden;
  if (SECONDARY_RELATIONS.has(e.type)) return showSecondary;
  return true;
}

export function Graph({ view }: { view: ViewGraph }) {
  const { selectedId, hoveredId, showSecondary, showForbidden, focus } = useAppState();
  const actions = useActions();
  const rf = useReactFlow();

  const relatedIds = useMemo(() => {
    const anchor = selectedId ?? hoveredId;
    return anchor ? NEIGHBORS.get(anchor) ?? new Set<string>() : new Set<string>();
  }, [selectedId, hoveredId]);

  const nodes: Node[] = useMemo(
    () =>
      view.nodes.map((n) => {
        const sel = n.id === selectedId;
        const rel = relatedIds.has(n.id);
        const data =
          n.kind === 'layer_group'
            ? { layerId: n.layer, count: n.memberCount ?? 0, dimmed: false, sel, rel }
            : { entity: n.entity, dimmed: n.dimmed, sel, rel };
        const rfNode: Node = {
          id: n.id,
          type: rfNodeType(n),
          position: n.position,
          data,
          style: { width: n.size.width, height: n.size.height },
          draggable: false,
          selectable: false,
          connectable: false,
        };
        return rfNode;
      }),
    [view.nodes, selectedId, relatedIds],
  );

  const edges: Edge[] = useMemo(() => {
    const focusActive = selectedId !== null;
    return view.edges
      .filter((e) => edgeVisible(e, selectedId, showSecondary, showForbidden))
      .map((e) => {
        const style = RELATION_STYLES[e.type];
        const incident = e.source === selectedId || e.target === selectedId;
        const dimmed = focusActive && !incident;
        const rfEdge: Edge = {
          id: e.id,
          source: e.source,
          target: e.target,
          type: 'flow',
          data: {
            relation: e.type,
            label: e.count > 1 && e.type === 'layer_flow' ? `${e.count}` : e.label,
            reason: e.reason,
            animated: style.animated,
            dimmed,
          },
          markerEnd:
            e.type === 'forbidden'
              ? undefined
              : { type: MarkerType.ArrowClosed, color: style.stroke, width: 14, height: 14 },
          zIndex: incident ? 10 : 0,
        };
        return rfEdge;
      });
  }, [view.edges, selectedId, showSecondary, showForbidden]);

  // Посадка вида: при первичном рендере и при изменении набора видимых узлов
  // (раскрытие/сворачивание слоёв). Пропускаем refit, пока активен фокус на узле.
  const layoutSig = view.nodes.length;
  useEffect(() => {
    if (focus) return; // при активном фокусе центрируем на узле, а не на всём графе
    const t = setTimeout(() => rf.fitView({ padding: 0.18, duration: 300 }), 0);
    return () => clearTimeout(t);
    // focus намеренно не в зависимостях: используется только как охранное условие текущего коммита
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layoutSig, rf]);

  // Фокус на конкретный узел (из поиска/инспектора).
  useEffect(() => {
    if (!focus) return;
    const node = view.nodes.find((n) => n.id === focus.id);
    if (node) {
      rf.setCenter(node.position.x + node.size.width / 2, node.position.y + node.size.height / 2, {
        zoom: 1.15,
        duration: 480,
      });
    }
    actions.clearFocus();
  }, [focus, view.nodes, rf, actions]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      defaultEdgeOptions={defaultEdgeOptions}
      minZoom={0.15}
      maxZoom={2.4}
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={false}
      panOnScroll
      proOptions={{ hideAttribution: true }}
      onNodeClick={(_, node) => {
        if (node.type === 'layer') actions.toggleLayer((node.data as { layerId: LayerId }).layerId);
        else actions.select(node.id);
      }}
      onNodeMouseEnter={(_, node) => {
        if (node.type !== 'layer') actions.hover(node.id);
      }}
      onNodeMouseLeave={() => actions.hover(null)}
      onPaneClick={() => actions.select(null)}
    >
      <Background variant={BackgroundVariant.Dots} gap={22} size={1} color="#e6ebf3" />
      <MiniMap
        pannable
        zoomable
        nodeStrokeWidth={2}
        nodeColor={(n) => {
          const layer = (n.data as { layerId?: keyof typeof LAYER_COLORS })?.layerId;
          const entity = (n.data as { entity?: { layer: keyof typeof LAYER_COLORS } })?.entity;
          const key = layer ?? entity?.layer ?? 'traffic';
          return LAYER_COLORS[key].accent;
        }}
        maskColor="rgba(248, 250, 253, 0.7)"
        style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10 }}
      />
      <Controls showInteractive={false} />
    </ReactFlow>
  );
}
