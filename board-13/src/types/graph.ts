/**
 * GRAPH MODEL — типизированное представление связей как графа.
 *
 * Узлы и рёбра НЕ хранят координат: раскладка вычисляется автоматически
 * (dagre). Добавление сущности в data/* перестраивает граф без ручной правки.
 */

import type { EntityKind, ID, Inspectable, LayerId } from './domain';

/** Семантический тип связи — управляет стилем ребра и фильтрацией. */
export type RelationType =
  | 'traffic_to_landing' // MK_ → PG_/LST_ (основная посадочная)
  | 'allowed_landing' // MK_ → допустимая посадочная
  | 'forbidden' // запрещённая связь (красный пунктир)
  | 'landing_to_event' // посадочная → целевое событие
  | 'flow_next' // шаг воронки → следующий шаг
  | 'emits_data' // платформа/посадочная → аналитика
  | 'analytics_flow' // узел аналитики → следующий узел
  | 'metric_to_decision' // метрика → решение
  | 'decision_to_target' // решение → объект воздействия (CELL)
  | 'cell_uses_channel' // CELL → источник
  | 'cell_uses_landing' // CELL → посадочная
  | 'cell_governed_by' // CELL ← метрика/решение (управляется)
  | 'contractor_instantiates' // шаблон → CELL
  | 'layer_flow'; // агрегированная связь между свёрнутыми слоями

/** Ребро доменного графа (до раскладки). Полностью типизировано. */
export interface GraphEdge {
  readonly id: ID;
  readonly source: ID;
  readonly target: ID;
  readonly type: RelationType;
  readonly label?: string;
  /** Причина запрета — только для type === 'forbidden'. */
  readonly reason?: string;
  /** Признак ставки на непроверенную гипотезу. */
  readonly hypothesis?: boolean;
}

/** Узел доменного графа (до раскладки). Несёт саму модель сущности. */
export interface GraphNode {
  readonly id: ID;
  readonly kind: EntityKind | 'layer_group';
  readonly layer: LayerId;
  /** Доменная модель. Для агрегированного узла слоя — отсутствует. */
  readonly entity?: Inspectable;
  /** Для агрегированного (свёрнутого) слоя: сколько сущностей внутри. */
  readonly memberCount?: number;
}

/** Полный доменный граф. */
export interface DomainGraph {
  readonly nodes: readonly GraphNode[];
  readonly edges: readonly GraphEdge[];
}

/** Прямоугольные габариты узла для раскладки. */
export interface NodeSize {
  readonly width: number;
  readonly height: number;
}

/** Позиция, назначенная алгоритмом раскладки. */
export interface Positioned {
  readonly x: number;
  readonly y: number;
}

/** Разрешённая связь для инспектора (родитель/потомок с подписью). */
export interface ResolvedRelation {
  readonly edge: GraphEdge;
  readonly node: GraphNode;
  readonly direction: 'incoming' | 'outgoing';
}

// ─── Представление (после сворачивания слоёв, фильтров и раскладки) ──────────

/** Узел представления: доменный узел или агрегат свёрнутого слоя, с позицией. */
export interface ViewNode extends GraphNode {
  readonly position: Positioned;
  readonly size: NodeSize;
  /** Приглушён фильтром (не совпал с активными фильтрами). */
  readonly dimmed: boolean;
  /** Свёрнут ли слой этого узла (для агрегата). */
  readonly collapsed: boolean;
}

/** Ребро представления: с учётом агрегации свёрнутых слоёв. */
export interface ViewEdge {
  readonly id: ID;
  readonly source: ID;
  readonly target: ID;
  /** Тип для стиля: агрегированные межслойные связи → layer_flow. */
  readonly type: RelationType;
  readonly label?: string;
  readonly reason?: string;
  readonly hypothesis?: boolean;
  /** Сколько доменных рёбер свернулось в это. */
  readonly count: number;
  /** Контекстное ребро (показывать только для выбранного узла). */
  readonly contextual: boolean;
}

export interface ViewGraph {
  readonly nodes: readonly ViewNode[];
  readonly edges: readonly ViewEdge[];
}
