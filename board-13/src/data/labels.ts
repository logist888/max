/**
 * Словари человекочитаемых подписей (data-слой).
 * Компоненты берут подписи отсюда — ни одной строки-словаря в JSX.
 */

import type {
  ActionKind,
  CellStatus,
  Confidence,
  EntityKind,
  FormationToken,
  FunnelSide,
  Language,
  LeverToken,
  Market,
  OwnerRole,
  ReactionSpeed,
  Temperature,
  UtmMedium,
} from '@/types';
import type { RelationType } from '@/types/graph';

export const MARKET_LABEL: Record<Market, string> = {
  CIS: 'СНГ',
  MENA: 'MENA',
  BOTH: 'СНГ + MENA',
};

export const LANGUAGE_LABEL: Record<Language, string> = {
  RU: 'Русский',
  EN: 'English',
  AR: 'العربية',
};

export const TEMPERATURE_LABEL: Record<Temperature, string> = {
  cold: 'Холодный',
  warm: 'Тёплый',
  hot: 'Горячий',
  nurture: 'Прогрев',
};

export const FORMATION_LABEL: Record<FormationToken, string> = {
  auction: 'Аукцион',
  recommendation: 'Рекомендация',
  search: 'Выдача / органика',
  base: 'База',
};

export const LEVER_LABEL: Record<LeverToken, string> = {
  budget: 'Бюджет',
  relations: 'Отношения',
  content: 'Контент',
  time: 'Время',
  brand: 'Бренд',
  base: 'База',
};

export const REACTION_SPEED_LABEL: Record<ReactionSpeed, string> = {
  hours: 'Часы',
  days: 'Дни',
  weeks: 'Недели',
  weeks_months: 'Недели–месяцы',
  months: 'Месяцы',
};

export const UTM_MEDIUM_LABEL: Record<UtmMedium, string> = {
  cpc: 'cpc',
  cpm: 'cpm',
  social: 'social',
  email: 'email',
  referral: 'referral',
  seo: 'seo',
  video: 'video',
  pr: 'pr',
  affiliate: 'affiliate',
  remarketing: 'remarketing',
};

export const OWNER_LABEL: Record<OwnerRole, string> = {
  marketing_lead: 'Маркетинг-лид',
  content_lead: 'Контент-лид',
  partner_lead: 'Партнёрский лид',
  crm_lead: 'CRM-лид',
  analyst: 'Аналитик',
  growth_lead: 'Growth-лид',
};

export const SIDE_LABEL: Record<FunnelSide, string> = {
  family: 'Семьи',
  expert: 'Эксперты',
};

export const STATUS_LABEL: Record<CellStatus, string> = {
  draft: 'Черновик',
  active: 'Активна',
  paused: 'Пауза',
  scaling: 'Масштабируется',
  stopped: 'Остановлена',
};

export const CONFIDENCE_LABEL: Record<Confidence, string> = {
  fact: 'Факт',
  estimate: 'Оценка',
  hypothesis: 'Гипотеза',
  target: 'Цель',
};

export const ACTION_LABEL: Record<ActionKind, string> = {
  fix_creative: 'Сменить креатив',
  fix_landing: 'Чинить посадочную',
  scale: 'Масштабировать',
  stop: 'Остановить',
  pause: 'Пауза',
  review_product: 'Разбор продукта',
  monitor: 'Мониторинг',
};

export const KIND_LABEL: Record<EntityKind, string> = {
  traffic_source: 'Источник трафика',
  landing: 'Посадочная',
  flow_step: 'Шаг воронки',
  analytics_node: 'Узел аналитики',
  metric: 'Метрика',
  decision: 'Решение',
  cell: 'Ячейка CELL',
  contractor: 'ТЗ подрядчику',
  rule: 'Правило связи',
};

export const RELATION_LABEL: Record<RelationType, string> = {
  traffic_to_landing: 'Основная посадочная',
  allowed_landing: 'Допустимая посадочная',
  forbidden: 'Запрещённая связь',
  landing_to_event: 'Целевое действие',
  flow_next: 'Следующий шаг',
  emits_data: 'Отдаёт данные',
  analytics_flow: 'Поток данных',
  metric_to_decision: 'Метрика → решение',
  decision_to_target: 'Действие на ячейку',
  cell_uses_channel: 'Канал ячейки',
  cell_uses_landing: 'Посадочная ячейки',
  cell_governed_by: 'Управляется решением',
  contractor_instantiates: 'Разворачивает ячейку',
  layer_flow: 'Связь слоёв',
};
