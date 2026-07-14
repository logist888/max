import type { NodeProps } from '@xyflow/react';
import { Icon } from '@/components/ui/Icon';
import { LAYER_COLORS } from '@/data/colors';
import { LAYER_BY_ID } from '@/data';
import { LAYER_ICON } from '@/data/visual';
import { NodeFrame } from './NodeFrame';
import type { LayerNodeData } from './nodeData';

/**
 * Свёрнутый слой — верхнеуровневый вид архитектуры (по умолчанию все слои свёрнуты).
 * Клик разворачивает слой (обрабатывается в Graph). Данные (название, кол-во) — из словаря слоёв.
 */
export function LayerGroupNode(props: NodeProps) {
  const { layerId, count, sel, rel } = props.data as unknown as LayerNodeData;
  const layer = LAYER_BY_ID.get(layerId);
  const color = LAYER_COLORS[layerId];
  if (!layer) return null;
  return (
    <NodeFrame accent={color.accent} className="node--layer" sel={sel} rel={rel} dimmed={false}>
      <div className="node__body" style={{ paddingRight: 92 }}>
        <div className="node__head">
          <span className="node__icon" style={{ background: color.soft, color: color.accent }}>
            <Icon name={LAYER_ICON[layerId]} size={16} />
          </span>
          <div style={{ minWidth: 0 }}>
            <div className="node__title" style={{ color: color.accent }}>{layer.title}</div>
            <div className="node__sub">{layer.subtitle}</div>
          </div>
        </div>
      </div>
      <div className="node__expand">
        <span className="count-badge">{count}</span>
        <Icon name="chevronDown" size={14} />
      </div>
    </NodeFrame>
  );
}
