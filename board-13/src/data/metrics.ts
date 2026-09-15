import type { Metric } from '@/types';

/**
 * Слой DECISIONS — метрики цикла решений (таблица Д.1). Пороги — целевые ориентиры [ЦЕЛЬ],
 * не замеры; калибруются после микро-теста E0 (docs/11). CR рег→заказ — [ГИПОТЕЗА].
 * Источник: docs/12-traffic-platform-decisions.md, блок Д.1.
 */
export const METRICS: readonly Metric[] = [
  {
    id: 'metric_cpl', kind: 'metric', layer: 'decisions', code: 'CPL', name: 'CPL / расход в день',
    description: 'Стоимость лида — быстрый прокси на раннем этапе, пока заказов мало.',
    dataSource: 'рекламный кабинет + Метрика', unit: '$/лид', confidence: 'target',
    thresholds: { green: '≤ $3', yellow: '$3–6', red: '> $6' }, checks: 'оценка входа канала (мониторинг)',
  },
  {
    id: 'metric_cr_landing', kind: 'metric', layer: 'decisions', code: 'CR_LANDING', name: 'CR посадочной',
    description: 'Клик → EVT_SCREENING_DONE / регистрация. Быстрый прокси качества квалификации.',
    dataSource: 'Метрика / платформа', unit: '%',
    thresholds: { green: '≥ 40%', yellow: '25–40%', red: '< 25%' }, checks: 'достаточно ли квалификации',
  },
  {
    id: 'metric_ctr', kind: 'metric', layer: 'decisions', code: 'CTR', name: 'CR креатива (CTR)',
    description: 'Показ → клик. Оценивается по бенчмарку канала.',
    dataSource: 'рекламный кабинет', unit: '%',
    thresholds: { green: 'выше бенчмарка', yellow: 'около бенчмарка', red: 'ниже бенчмарка' }, checks: 'качество креатива',
  },
  {
    id: 'metric_cr_order', kind: 'metric', layer: 'decisions', code: 'CR_ORDER', name: 'CR рег → ORDER_DIAG',
    description: 'Центральная ставка: подтверждается ли гипотеза скрининга на холодном трафике.',
    dataSource: 'платформа', unit: '%', confidence: 'hypothesis',
    thresholds: { green: '≥ 5%', yellow: '3–5%', red: '< 3%' }, checks: 'подтверждается ли гипотеза скрининга',
  },
  {
    id: 'metric_drr', kind: 'metric', layer: 'decisions', code: 'DRR', name: 'ДРР (расход / выручка)',
    description: 'Главный KPI цикла. Требует сшивки client_id→user_id и импорта расхода (блок Г.3).',
    dataSource: 'кабинет (расход) + платформа (выручка) через сшивку', unit: '%',
    thresholds: { green: '≤ 20%', yellow: '20–35%', red: '> 35%' }, checks: 'экономика канала',
  },
  {
    id: 'metric_returns', kind: 'metric', layer: 'decisions', code: 'RETURNS', name: 'Возвраты / отказ от заказа',
    description: 'Прокси доверия к автопродукту. Рост → разбор продукта, не трафика.',
    dataSource: 'платформа', unit: '%', confidence: 'hypothesis',
    thresholds: { green: '≤ базового', yellow: 'около базового', red: '> базового' }, checks: 'доверие к автопродукту',
  },
];
