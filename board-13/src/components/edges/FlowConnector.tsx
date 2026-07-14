import { BaseEdge, EdgeLabelRenderer, getSmoothStepPath, type EdgeProps, type EdgeTypes } from '@xyflow/react';
import { RELATION_STYLES } from '@/data/colors';
import type { RelationType } from '@/types/graph';

export interface FlowEdgeData {
  readonly relation: RelationType;
  readonly label?: string;
  readonly reason?: string;
  readonly animated: boolean;
  readonly dimmed: boolean;
  [key: string]: unknown;
}

/**
 * Кастомный коннектор: плавная ступенчатая линия, стиль берётся из RELATION_STYLES по типу связи.
 * Подпись и причина запрета выводятся поверх ребра.
 */
export function FlowConnector(props: EdgeProps) {
  const { sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, markerEnd, id } = props;
  const data = (props.data ?? {}) as FlowEdgeData;
  const rel = data.relation ?? 'layer_flow';
  const style = RELATION_STYLES[rel];
  const [path, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    borderRadius: 12,
  });

  const isForbidden = rel === 'forbidden';
  const cls = data.animated ? 'edge-path edge-path--animated' : 'edge-path';

  return (
    <>
      <BaseEdge
        id={id}
        path={path}
        markerEnd={markerEnd}
        className={cls}
        style={{
          stroke: style.stroke,
          strokeWidth: style.width,
          strokeDasharray: style.dashed ? '5 4' : undefined,
          opacity: data.dimmed ? 0.12 : 1,
        }}
      />
      {(data.label || isForbidden) && !data.dimmed && (
        <EdgeLabelRenderer>
          <div
            className={isForbidden ? 'edge-label edge-label--forbidden' : 'edge-label'}
            style={{ transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)` }}
            title={data.reason ?? data.label}
          >
            {isForbidden ? '✕ запрет' : data.label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export const edgeTypes: EdgeTypes = { flow: FlowConnector };
