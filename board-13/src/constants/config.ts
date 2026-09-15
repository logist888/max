/**
 * Конфигурация приложения (не данные предметной области).
 * Габариты узлов, параметры раскладки, категории видимости рёбер, метаданные борда.
 */

import type { EntityKind, LayerId } from '@/types';
import type { NodeSize } from '@/types/graph';
import type { RelationType } from '@/types/graph';

export const APP_META = {
  boardNo: 13,
  title: 'Борд 13 · System Map',
  subtitle: 'Traffic → Platform → Decisions',
  product: 'MainExperts',
  scope: 'Поток-2 (воронка семей)',
  version: '1.0.0',
  source: 'docs/12-traffic-platform-decisions.md',
  sourceDate: '08.07.2026',
} as const;

/**
 * Параметры детерминированной слоистой (swimlane) авто-раскладки.
 * Раскладка выводится из layer.order и состава узлов — координаты вручную не задаются,
 * схема перестраивается при любом изменении данных. Порядок внутри полосы уменьшает
 * пересечения барицентром (см. utils/layout.ts).
 */
export const LAYOUT = {
  /** Вертикальный зазор между полосами слоёв. */
  bandGap: 116,
  /** Горизонтальный зазор между узлами внутри полосы. */
  nodeGap: 30,
  /** Число проходов барицентром для уменьшения пересечений рёбер. */
  orderingPasses: 6,
} as const;

/** Габариты узлов по типу сущности (для dagre; координаты вручную не задаются). */
export const NODE_SIZES: Record<EntityKind | 'layer_group', NodeSize> = {
  traffic_source: { width: 216, height: 96 },
  landing: { width: 216, height: 104 },
  flow_step: { width: 196, height: 92 },
  analytics_node: { width: 216, height: 96 },
  metric: { width: 212, height: 104 },
  decision: { width: 212, height: 92 },
  cell: { width: 248, height: 132 },
  contractor: { width: 300, height: 132 },
  rule: { width: 200, height: 80 },
  layer_group: { width: 360, height: 96 },
};

/** Рёбра, видимые всегда (когда оба конца видимы). */
export const ALWAYS_RELATIONS: ReadonlySet<RelationType> = new Set<RelationType>([
  'traffic_to_landing',
  'landing_to_event',
  'flow_next',
  'analytics_flow',
  'metric_to_decision',
  'layer_flow',
]);

/** Дополнительные структурные рёбра (тумблер «Доп. связи»). */
export const SECONDARY_RELATIONS: ReadonlySet<RelationType> = new Set<RelationType>([
  'allowed_landing',
  'emits_data',
]);

/** Запрещённые связи (тумблер «Запреты»). */
export const FORBIDDEN_RELATIONS: ReadonlySet<RelationType> = new Set<RelationType>(['forbidden']);

/** Контекстные рёбра — показываются только для выбранного/наведённого узла. */
export const CONTEXTUAL_RELATIONS: ReadonlySet<RelationType> = new Set<RelationType>([
  'decision_to_target',
  'cell_uses_channel',
  'cell_uses_landing',
  'cell_governed_by',
  'contractor_instantiates',
]);

/** По умолчанию все слои свёрнуты — пользователь видит архитектуру за 30 секунд. */
export const DEFAULT_EXPANDED_LAYERS: readonly LayerId[] = [];

/** Порог, ниже которого бюджет ячейки нарушает правило (для валидации/подсветки). */
export const MIN_CELL_BUDGET_USD = 400;
