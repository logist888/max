import { motion } from 'framer-motion';
import type { RelationType } from '@/types/graph';
import type { CellStatus, Confidence, Temperature } from '@/types';
import { useActions } from '@/app/store';
import { LAYERS } from '@/data';
import {
  CONFIDENCE_COLORS,
  LAYER_COLORS,
  RELATION_STYLES,
  STATUS_COLORS,
  TEMPERATURE_COLORS,
} from '@/data/colors';
import {
  CONFIDENCE_LABEL,
  RELATION_LABEL,
  STATUS_LABEL,
  TEMPERATURE_LABEL,
} from '@/data/labels';
import { IconButton } from '@/components/ui/IconButton';

const RELATIONS: readonly RelationType[] = [
  'traffic_to_landing',
  'allowed_landing',
  'forbidden',
  'landing_to_event',
  'flow_next',
  'emits_data',
  'analytics_flow',
  'metric_to_decision',
  'decision_to_target',
  'cell_uses_channel',
  'layer_flow',
];

const TEMPERATURES: readonly Temperature[] = ['cold', 'warm', 'hot', 'nurture'];
const STATUSES: readonly CellStatus[] = ['active', 'scaling', 'paused', 'stopped', 'draft'];
const CONFIDENCES: readonly Confidence[] = ['fact', 'estimate', 'hypothesis', 'target'];

/** Легенда: все цвета слоёв, типы стрелок, состояния и метки достоверности. */
export function Legend() {
  const actions = useActions();
  return (
    <motion.div
      className="panel legend"
      initial={{ y: 12, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.16 }}
    >
      <div className="legend__inner">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <strong style={{ fontSize: 12.5 }}>Легенда</strong>
          <IconButton icon="x" title="Закрыть легенду" ghost onClick={() => actions.setLegendOpen(false)} />
        </div>

        <div className="section__title">Слои (сверху вниз)</div>
        {LAYERS.map((l) => (
          <div className="legend__row" key={l.id}>
            <span className="legend__swatch" style={{ background: LAYER_COLORS[l.id].accent }} />
            {l.title}
          </div>
        ))}

        <div className="section__title" style={{ marginTop: 14 }}>Связи</div>
        {RELATIONS.map((r) => {
          const s = RELATION_STYLES[r];
          return (
            <div className="legend__row" key={r}>
              <svg width={24} height={8} style={{ flexShrink: 0 }}>
                <line
                  x1={0}
                  y1={4}
                  x2={24}
                  y2={4}
                  stroke={s.stroke}
                  strokeWidth={Math.max(s.width, 1.5)}
                  strokeDasharray={s.dashed ? '4 3' : undefined}
                />
              </svg>
              {RELATION_LABEL[r]}
              {s.animated && <span className="muted" style={{ fontSize: 10 }}>· поток</span>}
            </div>
          );
        })}

        <div className="section__title" style={{ marginTop: 14 }}>Температура трафика</div>
        {TEMPERATURES.map((t) => (
          <div className="legend__row" key={t}>
            <span className="legend__swatch" style={{ background: TEMPERATURE_COLORS[t] }} />
            {TEMPERATURE_LABEL[t]}
          </div>
        ))}

        <div className="section__title" style={{ marginTop: 14 }}>Статус ячейки</div>
        {STATUSES.map((st) => (
          <div className="legend__row" key={st}>
            <span className="legend__swatch" style={{ background: STATUS_COLORS[st] }} />
            {STATUS_LABEL[st]}
          </div>
        ))}

        <div className="section__title" style={{ marginTop: 14 }}>Достоверность</div>
        {CONFIDENCES.map((c) => (
          <div className="legend__row" key={c}>
            <span className="legend__swatch" style={{ background: CONFIDENCE_COLORS[c] }} />
            {CONFIDENCE_LABEL[c]}
          </div>
        ))}
      </div>
    </motion.div>
  );
}
