import type { NodeProps } from '@xyflow/react';
import { Icon } from '@/components/ui/Icon';
import { presentEntity } from '@/utils/present';
import { NodeFrame } from './NodeFrame';
import type { EntityNodeData } from './nodeData';

/**
 * Универсальная карточка сущности. Не знает про MK/PG/EVT — берёт иконку/цвет/метки
 * из presentEntity. Одна карточка обслуживает источники, посадочные, шаги, аналитику, метрики, решения.
 */
export function EntityNode(props: NodeProps) {
  const { entity, dimmed, sel, rel } = props.data as unknown as EntityNodeData;
  const { iconKey, color, tags } = presentEntity(entity);
  return (
    <NodeFrame accent={color.accent} sel={sel} rel={rel} dimmed={dimmed}>
      <div className="node__body">
        <div className="node__head">
          <span className="node__icon" style={{ background: color.soft, color: color.accent }}>
            <Icon name={iconKey} size={15} />
          </span>
          <div style={{ minWidth: 0 }}>
            <div className="node__code">{entity.code}</div>
            <div className="node__name">{entity.name}</div>
          </div>
        </div>
        {tags.length > 0 && (
          <div className="node__meta">
            {tags.map((t, i) => (
              <span
                key={i}
                className="node__tag"
                title={t.title}
                style={t.color ? { color: t.color, background: `${t.color}14` } : undefined}
              >
                {t.label}
              </span>
            ))}
          </div>
        )}
      </div>
    </NodeFrame>
  );
}
