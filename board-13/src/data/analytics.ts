import type { AnalyticsNode } from '@/types';

/**
 * Слой ANALYTICS — учётный контур (блок Г). Поток данных:
 * Рекламная площадка → GA/Метрика → Платформа → Витрина → Дашборд → Decision Engine.
 * Рёбра analytics_flow строятся по возрастанию order; подпись — flowLabel.
 * gap — то, что «не измеряется сейчас автоматически» (раздел «Пробелы контура»).
 * Источник: docs/12-traffic-platform-decisions.md, блок Г + «Что не измеряется сейчас».
 */
export const ANALYTICS_NODES: readonly AnalyticsNode[] = [
  {
    id: 'an_ad_platform', kind: 'analytics_node', layer: 'analytics', code: 'AD_PLATFORM',
    name: 'Рекламная площадка', description: 'VK / Meta / Яндекс / Google. Показы, клики, расход кампаний.',
    nodeKind: 'ad_platform', order: 1, iconKey: 'broadcast', holds: 'показы, клики, расход по кампаниям',
    gap: 'Расход не импортируется автоматически — нужен импорт в единую витрину.',
    flowLabel: 'клики, показы, пиксель',
  },
  {
    id: 'an_web_analytics', kind: 'analytics_node', layer: 'analytics', code: 'WEB_ANALYTICS',
    name: 'GA / Яндекс.Метрика', description: 'Веб-аналитика. Клики, показы, сессии, CPL, CR посадочной до регистрации.',
    nodeKind: 'web_analytics', order: 2, iconKey: 'barChart', holds: 'клики, сессии, CPL, CR посадочной (до рег.)',
    confidence: 'fact', flowLabel: 'client_id / UTM при EVT_REG',
  },
  {
    id: 'an_platform', kind: 'analytics_node', layer: 'analytics', code: 'PLATFORM',
    name: 'Платформа (Rust)', description: 'Append-only факты: EVT_REG, EVT_PROFILE10, ORDER_DIAG, членство, ORDER_RENEW, LTV.',
    nodeKind: 'platform', order: 3, iconKey: 'server', holds: 'EVT_*/ORDER_* факты, членство, LTV',
    confidence: 'fact', flowLabel: 'append-only факты EVT_/ORDER_',
  },
  {
    id: 'an_warehouse', kind: 'analytics_node', layer: 'analytics', code: 'WAREHOUSE',
    name: 'Единая витрина', description: 'Импорт расхода + сшивка client_id → user_id. Точка, где считается истинный ДРР.',
    nodeKind: 'warehouse', order: 4, iconKey: 'database', holds: 'расход × выручка, сквозная атрибуция, ДРР',
    gap: 'Витрина и сшивка client_id→user_id не построены — главный технический блокер контура.',
    confidence: 'target', flowLabel: 'ДРР, LTV, когорты',
  },
  {
    id: 'an_dashboard', kind: 'analytics_node', layer: 'analytics', code: 'DASHBOARD',
    name: 'Дашборд', description: 'KPI, тренды, светофор порогов по каждой ячейке.',
    nodeKind: 'dashboard', order: 5, iconKey: 'dashboard', holds: 'KPI, светофор, тренды',
    flowLabel: 'светофор порогов',
  },
  {
    id: 'an_decision_engine', kind: 'analytics_node', layer: 'analytics', code: 'DECISION_ENGINE',
    name: 'Decision Engine', description: 'Метрика → порог → решение → действие. Применяется к каждой ячейке CELL_.',
    nodeKind: 'decision_engine', order: 6, iconKey: 'cpu', holds: 'правила метрика → порог → действие',
    feedsInto: ['metric_cpl', 'metric_cr_landing', 'metric_ctr', 'metric_cr_order', 'metric_drr', 'metric_returns'],
  },
];
