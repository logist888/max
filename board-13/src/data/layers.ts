import type { LayerDef } from '@/types';

/**
 * Архитектурные слои сверху вниз (блоки А–Д документа 12 + шаблон подрядчику).
 * TRAFFIC → LANDINGS → PLATFORM → ANALYTICS → DECISIONS → CELL → CONTRACTOR.
 */
export const LAYERS: readonly LayerDef[] = [
  {
    id: 'traffic',
    order: 0,
    title: 'TRAFFIC',
    subtitle: 'Источники трафика · словарь MK_',
    kinds: ['traffic_source'],
  },
  {
    id: 'landings',
    order: 1,
    title: 'LANDINGS',
    subtitle: 'Посадочные PG_ / LST_ · правила связей',
    kinds: ['landing', 'rule'],
  },
  {
    id: 'platform',
    order: 2,
    title: 'PLATFORM',
    subtitle: 'Пользовательский поток · события EVT_ / заказы ORDER_',
    kinds: ['flow_step'],
  },
  {
    id: 'analytics',
    order: 3,
    title: 'ANALYTICS',
    subtitle: 'Учётный контур · поток данных',
    kinds: ['analytics_node'],
  },
  {
    id: 'decisions',
    order: 4,
    title: 'DECISIONS',
    subtitle: 'Метрика → порог → решение → действие',
    kinds: ['metric', 'decision'],
  },
  {
    id: 'cell',
    order: 5,
    title: 'CELL',
    subtitle: 'Измерительные ячейки — центральный объект системы',
    kinds: ['cell'],
  },
  {
    id: 'contractor',
    order: 6,
    title: 'CONTRACTOR',
    subtitle: 'Шаблон запуска подрядчику',
    kinds: ['contractor'],
  },
];

export const LAYER_BY_ID: ReadonlyMap<string, LayerDef> = new Map(
  LAYERS.map((l) => [l.id, l]),
);
