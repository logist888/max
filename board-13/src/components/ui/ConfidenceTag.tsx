import type { Confidence } from '@/types';
import { CONFIDENCE_COLORS } from '@/data/colors';
import { CONFIDENCE_LABEL } from '@/data/labels';

/** Метка достоверности (правило данных проекта: факт/оценка/гипотеза/цель). */
export function ConfidenceTag({ confidence }: { confidence: Confidence }) {
  const color = CONFIDENCE_COLORS[confidence];
  return (
    <span
      className="chip chip--dot"
      style={{ color, borderColor: `${color}44`, background: `${color}12` }}
    >
      {CONFIDENCE_LABEL[confidence]}
    </span>
  );
}
