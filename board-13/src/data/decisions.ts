import type { Decision } from '@/types';

/**
 * Слой DECISIONS — дерево решений (Decision Engine, раздел DECISION ENGINE + таблица Д.1).
 * Каждое решение: метрика → триггер/порог → действие. Порядок принятия: сначала быстрые
 * прокси (CPL, CR посадочной — дни), затем CR рег→заказ и ДРР (недели). Масштабировать только
 * по CPL нельзя — там живёт непроверенная гипотеза скрининга [ГИПОТЕЗА].
 * Источник: docs/12-traffic-platform-decisions.md, блок Д.1 + раздел DECISION ENGINE.
 */
export const DECISIONS: readonly Decision[] = [
  {
    id: 'dec_monitor', kind: 'decision', layer: 'decisions', code: 'DEC_MONITOR', name: 'Мониторинг входа',
    description: 'CPL в норме — канал наблюдается, дешёвый лид ≠ оплата. Решение о судьбе — по ДРР.',
    metricId: 'metric_cpl', trigger: 'green', condition: 'CPL ≤ $3 (зелёный)',
    action: 'monitor', actionLabel: 'Мониторинг — оценка входа',
  },
  {
    id: 'dec_fix_creative', kind: 'decision', layer: 'decisions', code: 'DEC_FIX_CREATIVE', name: 'Сменить креатив',
    description: 'CTR ниже бенчмарка канала — проблема на уровне креатива.',
    metricId: 'metric_ctr', trigger: 'below', condition: 'CTR ↓ (ниже бенчмарка)',
    action: 'fix_creative', actionLabel: 'Сменить креатив',
  },
  {
    id: 'dec_fix_landing', kind: 'decision', layer: 'decisions', code: 'DEC_FIX_LANDING', name: 'Чинить посадочную',
    description: 'CR посадочной < 25% — квалификация проседает на посадочной.',
    metricId: 'metric_cr_landing', trigger: 'below', condition: 'CR посадочной ↓ (< 25%)',
    action: 'fix_landing', actionLabel: 'Чинить посадочную',
  },
  {
    id: 'dec_pause_offer', kind: 'decision', layer: 'decisions', code: 'DEC_PAUSE_OFFER', name: 'Пауза, разбор оффера',
    description: 'CR рег→заказ < 3% — гипотеза скрининга не подтверждается. Разбор оффера, не креатива.',
    metricId: 'metric_cr_order', trigger: 'below', condition: 'CR рег→заказ ↓ (< 3%)',
    action: 'pause', actionLabel: 'Пауза, разбор оффера', hypothesis: true,
  },
  {
    id: 'dec_scale', kind: 'decision', layer: 'decisions', code: 'DEC_SCALE', name: 'Масштабировать',
    description: 'ДРР ≤ 20% и объём есть — экономика канала здоровая. Масштабируем ячейку.',
    metricId: 'metric_drr', trigger: 'green', condition: 'ДРР ≤ 20% + объём есть',
    action: 'scale', actionLabel: 'Масштабировать',
  },
  {
    id: 'dec_stop', kind: 'decision', layer: 'decisions', code: 'DEC_STOP', name: 'Остановить CELL',
    description: 'ДРР > 35% — канал убыточен. Останавливаем ячейку.',
    metricId: 'metric_drr', trigger: 'red', condition: 'ДРР ↑ (> 35%)',
    action: 'stop', actionLabel: 'Остановить CELL',
  },
  {
    id: 'dec_review_product', kind: 'decision', layer: 'decisions', code: 'DEC_REVIEW_PRODUCT', name: 'Разбор продукта',
    description: 'Возвраты выше базового — падает доверие к автопродукту. Разбор продукта, не трафика.',
    metricId: 'metric_returns', trigger: 'above', condition: 'Возвраты ↑ (> базового)',
    action: 'review_product', actionLabel: 'Разбор продукта', hypothesis: true,
  },
];
