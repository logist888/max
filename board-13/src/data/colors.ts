/**
 * Цветовые токены (data-слой). Единственное место, где живут цвета системы.
 * Палитра сдержанная (Linear / Stripe / Vercel): белый фон, тонкие линии, акцент на читаемости.
 */

import type {
  CellStatus,
  Confidence,
  EntityKind,
  LayerId,
  Temperature,
} from '@/types';
import type { RelationType } from '@/types/graph';

export interface ColorToken {
  /** Основной акцент (обводка, иконка). */
  readonly accent: string;
  /** Мягкая заливка карточки. */
  readonly soft: string;
  /** Обводка карточки в покое. */
  readonly border: string;
}

export const LAYER_COLORS: Record<LayerId, ColorToken> = {
  traffic: { accent: '#6366f1', soft: '#eef2ff', border: '#e0e7ff' },
  landings: { accent: '#0ea5e9', soft: '#f0f9ff', border: '#e0f2fe' },
  platform: { accent: '#10b981', soft: '#ecfdf5', border: '#d1fae5' },
  analytics: { accent: '#f59e0b', soft: '#fffbeb', border: '#fef3c7' },
  decisions: { accent: '#f43f5e', soft: '#fff1f2', border: '#ffe4e6' },
  cell: { accent: '#7c3aed', soft: '#f5f3ff', border: '#ede9fe' },
  contractor: { accent: '#475569', soft: '#f8fafc', border: '#e2e8f0' },
};

/** Цвет по типу сущности (наследует акцент своего слоя, кроме CELL). */
export const KIND_COLORS: Record<EntityKind, ColorToken> = {
  traffic_source: LAYER_COLORS.traffic,
  landing: LAYER_COLORS.landings,
  flow_step: LAYER_COLORS.platform,
  analytics_node: LAYER_COLORS.analytics,
  metric: LAYER_COLORS.decisions,
  decision: LAYER_COLORS.decisions,
  cell: LAYER_COLORS.cell,
  contractor: LAYER_COLORS.contractor,
  rule: LAYER_COLORS.landings,
};

export const TEMPERATURE_COLORS: Record<Temperature, string> = {
  cold: '#3b82f6',
  warm: '#f59e0b',
  hot: '#ef4444',
  nurture: '#8b5cf6',
};

export const STATUS_COLORS: Record<CellStatus, string> = {
  draft: '#94a3b8',
  active: '#10b981',
  paused: '#f59e0b',
  scaling: '#3b82f6',
  stopped: '#ef4444',
};

export const CONFIDENCE_COLORS: Record<Confidence, string> = {
  fact: '#10b981',
  estimate: '#f59e0b',
  hypothesis: '#f43f5e',
  target: '#6366f1',
};

export interface EdgeStyle {
  readonly stroke: string;
  readonly dashed: boolean;
  readonly animated: boolean;
  readonly width: number;
}

export const RELATION_STYLES: Record<RelationType, EdgeStyle> = {
  traffic_to_landing: { stroke: '#94a3b8', dashed: false, animated: false, width: 1.5 },
  allowed_landing: { stroke: '#cbd5e1', dashed: true, animated: false, width: 1 },
  forbidden: { stroke: '#ef4444', dashed: true, animated: false, width: 1.5 },
  landing_to_event: { stroke: '#38bdf8', dashed: false, animated: false, width: 1.5 },
  flow_next: { stroke: '#10b981', dashed: false, animated: false, width: 1.75 },
  emits_data: { stroke: '#f59e0b', dashed: true, animated: true, width: 1.25 },
  analytics_flow: { stroke: '#f59e0b', dashed: false, animated: true, width: 1.75 },
  metric_to_decision: { stroke: '#f43f5e', dashed: false, animated: false, width: 1.5 },
  decision_to_target: { stroke: '#7c3aed', dashed: false, animated: false, width: 1.5 },
  cell_uses_channel: { stroke: '#a78bfa', dashed: true, animated: false, width: 1 },
  cell_uses_landing: { stroke: '#a78bfa', dashed: true, animated: false, width: 1 },
  cell_governed_by: { stroke: '#f43f5e', dashed: true, animated: false, width: 1 },
  contractor_instantiates: { stroke: '#475569', dashed: true, animated: false, width: 1 },
  layer_flow: { stroke: '#cbd5e1', dashed: false, animated: false, width: 2 },
};

/** Нейтральные токены интерфейса. */
export const UI = {
  bg: '#ffffff',
  canvasBg: '#fbfcfe',
  ink: '#0f172a',
  inkSoft: '#475569',
  inkFaint: '#94a3b8',
  line: '#e2e8f0',
  lineSoft: '#f1f5f9',
  focus: '#6366f1',
} as const;
