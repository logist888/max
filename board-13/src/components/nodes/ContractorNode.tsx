import type { NodeProps } from '@xyflow/react';
import { Icon } from '@/components/ui/Icon';
import { LAYER_COLORS } from '@/data/colors';
import { NodeFrame } from './NodeFrame';
import type { ContractorNodeData } from './nodeData';

/** Шаблон ТЗ подрядчику — последний слой. Разворачивает ячейку в реальный запуск. */
export function ContractorNode(props: NodeProps) {
  const { entity, dimmed, sel, rel } = props.data as unknown as ContractorNodeData;
  const accent = LAYER_COLORS.contractor.accent;
  return (
    <NodeFrame accent={accent} className="node--contractor" sel={sel} rel={rel} dimmed={dimmed}>
      <div className="node__body">
        <div className="node__head">
          <span className="node__icon" style={{ background: LAYER_COLORS.contractor.soft, color: accent }}>
            <Icon name="clipboard" size={15} />
          </span>
          <div style={{ minWidth: 0 }}>
            <div className="node__code">{entity.code}</div>
            <div className="node__name">{entity.name}</div>
          </div>
        </div>
        <div className="node__meta">
          <span className="node__tag">{entity.fields.length} полей</span>
          <span className="node__tag">{entity.prohibitions.length} запретов</span>
          <span className="node__tag" style={{ color: '#b91c1c', background: '#fef2f2' }}>стоп-правило</span>
        </div>
      </div>
    </NodeFrame>
  );
}
