/**
 * Единая точка сборки данных предметной области.
 * Всё знание системы приходит отсюда; компоненты не импортируют отдельные словари напрямую.
 */

import type { DomainEntity, ID, Inspectable } from '@/types';
import { TRAFFIC_SOURCES } from './traffic';
import { LANDINGS } from './landings';
import { FLOW_STEPS } from './events';
import { ANALYTICS_NODES } from './analytics';
import { METRICS } from './metrics';
import { DECISIONS } from './decisions';
import { CELLS } from './cells';
import { CONTRACTORS } from './contractor';
import { RULES } from './rules';
import { LAYERS } from './layers';

export { TRAFFIC_SOURCES } from './traffic';
export { LANDINGS } from './landings';
export { FLOW_STEPS } from './events';
export { ANALYTICS_NODES } from './analytics';
export { METRICS } from './metrics';
export { DECISIONS } from './decisions';
export { CELLS } from './cells';
export { CONTRACTORS } from './contractor';
export { RULES } from './rules';
export { LAYERS, LAYER_BY_ID } from './layers';

/** Все узловые сущности графа (без правил — правила порождают рёбра). */
export const ALL_ENTITIES: readonly DomainEntity[] = [
  ...TRAFFIC_SOURCES,
  ...LANDINGS,
  ...FLOW_STEPS,
  ...ANALYTICS_NODES,
  ...METRICS,
  ...DECISIONS,
  ...CELLS,
  ...CONTRACTORS,
];

/** Всё, что можно выбрать и показать в инспекторе (узлы + правила). */
export const ALL_INSPECTABLES: readonly Inspectable[] = [...ALL_ENTITIES, ...RULES];

/** Индекс по id для быстрого разрешения ссылок. */
export const ENTITY_BY_ID: ReadonlyMap<ID, Inspectable> = new Map(
  ALL_INSPECTABLES.map((e) => [e.id, e]),
);

export const LAYER_COUNT = LAYERS.length;
