import type { NodeProps } from '@xyflow/react';
import { Icon } from '@/components/ui/Icon';
import { LAYER_COLORS, STATUS_COLORS } from '@/data/colors';
import { LANGUAGE_LABEL, MARKET_LABEL, OWNER_LABEL, STATUS_LABEL } from '@/data/labels';
import { NodeFrame } from './NodeFrame';
import type { CellNodeData } from './nodeData';

/**
 * CELL — центральный объект системы, визуально выделен (класс node--cell).
 * Все решения принимаются относительно ячейки, поэтому карточка несёт статус, рынок,
 * язык, бюджет и владельца.
 */
export function CellNode(props: NodeProps) {
  const { entity, dimmed, sel, rel } = props.data as unknown as CellNodeData;
  const accent = LAYER_COLORS.cell.accent;
  const statusColor = STATUS_COLORS[entity.status];
  return (
    <NodeFrame accent={accent} className="node--cell" sel={sel} rel={rel} dimmed={dimmed}>
      <div className="node__body">
        <div className="node__head">
          <span className="node__icon" style={{ background: LAYER_COLORS.cell.soft, color: accent }}>
            <Icon name="cell" size={15} />
          </span>
          <div style={{ minWidth: 0 }}>
            <div className="node__code">{entity.code}</div>
            <div className="node__name">{entity.name}</div>
          </div>
        </div>
        <div className="node__meta">
          <span className="node__tag" title="Статус" style={{ color: statusColor, background: `${statusColor}16` }}>
            {STATUS_LABEL[entity.status]}
          </span>
          <span className="node__tag" title="Рынок">{MARKET_LABEL[entity.market]}</span>
          <span className="node__tag" title="Язык">{LANGUAGE_LABEL[entity.language]}</span>
        </div>
        <div className="node__code" style={{ marginTop: 'auto' }}>
          ${entity.budgetUsd} · {OWNER_LABEL[entity.owner]}
        </div>
      </div>
    </NodeFrame>
  );
}
