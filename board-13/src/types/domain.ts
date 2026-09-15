/**
 * DOMAIN MODEL — единственный источник истины системы.
 *
 * Строгие типы всех сущностей слоя «Трафик → Платформа → Решения».
 * Источник данных — docs/12-traffic-platform-decisions.md (снимок 08.07.2026).
 *
 * Компоненты презентационного слоя не знают о конкретных MK/PG/CELL —
 * они умеют отображать только эти модели. `any` запрещён во всём проекте.
 */

// ─────────────────────────────────────────────────────────────────────────────
// Базовые примитивы
// ─────────────────────────────────────────────────────────────────────────────

export type ID = string;

/** Рынки Потока-2. */
export type Market = 'CIS' | 'MENA' | 'BOTH';

/** Языки креатива/посадочной. */
export type Language = 'RU' | 'EN' | 'AR';

/**
 * Температура трафика (готовность к покупке). Диапазоны из матрицы (В)
 * нормализуются к первичному бакету; исходная подпись сохраняется в `label`.
 */
export type Temperature = 'cold' | 'warm' | 'hot' | 'nurture';

/** Как формируется трафик (блок А). */
export type FormationToken = 'auction' | 'recommendation' | 'search' | 'base';

/** Рычаг управления каналом (блок А). */
export type LeverToken = 'budget' | 'relations' | 'content' | 'time' | 'brand' | 'base';

/** Скорость отклика канала на управляющее воздействие (блок А). */
export type ReactionSpeed = 'hours' | 'days' | 'weeks' | 'weeks_months' | 'months';

/** Канонический тип utm_medium (закрытый список, блок Г.1). */
export type UtmMedium =
  | 'cpc'
  | 'cpm'
  | 'social'
  | 'email'
  | 'referral'
  | 'seo'
  | 'video'
  | 'pr'
  | 'affiliate'
  | 'remarketing';

/** Роль-владелец решения (обезличена, по направлениям; блок Д.2). */
export type OwnerRole =
  | 'marketing_lead'
  | 'content_lead'
  | 'partner_lead'
  | 'crm_lead'
  | 'analyst'
  | 'growth_lead';

/** Сторона воронки. Метрики сторон не агрегируются (жёсткое правило проекта). */
export type FunnelSide = 'family' | 'expert';

/** Статус измерительной ячейки CELL_ (производный от таблицы решений Д.1). */
export type CellStatus = 'draft' | 'active' | 'paused' | 'scaling' | 'stopped';

/** Пометка достоверности факта (правило данных проекта). */
export type Confidence = 'fact' | 'estimate' | 'hypothesis' | 'target';

/** Идентификатор архитектурного слоя (сверху вниз). */
export type LayerId =
  | 'traffic'
  | 'landings'
  | 'platform'
  | 'analytics'
  | 'decisions'
  | 'cell'
  | 'contractor';

/** Дискриминатор типа сущности — единый реестр для графа, инспектора, легенды. */
export type EntityKind =
  | 'traffic_source'
  | 'landing'
  | 'flow_step'
  | 'analytics_node'
  | 'metric'
  | 'decision'
  | 'cell'
  | 'contractor'
  | 'rule';

// ─────────────────────────────────────────────────────────────────────────────
// Общий контракт сущности
// ─────────────────────────────────────────────────────────────────────────────

/** Запись истории изменений (структура предусмотрена; данных пока может не быть). */
export interface ChangeRecord {
  readonly date: string; // ISO
  readonly author: string;
  readonly summary: string;
}

/** Базовые поля любой доменной сущности. Используется инспектором и поиском. */
export interface BaseEntity {
  readonly id: ID;
  readonly kind: EntityKind;
  readonly layer: LayerId;
  /** Машинный код (MK_/PG_/EVT_/CELL_ …) либо стабильный слаг. */
  readonly code: string;
  /** Человекочитаемое название. */
  readonly name: string;
  readonly description?: string;
  readonly confidence?: Confidence;
  readonly history?: readonly ChangeRecord[];
}

// ─────────────────────────────────────────────────────────────────────────────
// TRAFFIC — источник трафика (MK_*) + реф-ссылка (REF_*)
// ─────────────────────────────────────────────────────────────────────────────

export interface TrafficSource extends BaseEntity {
  readonly kind: 'traffic_source';
  readonly layer: 'traffic';
  readonly market: Market;
  readonly temperature: Temperature;
  /** Исходная подпись температуры, если это диапазон («холод–тёпл»). */
  readonly temperatureLabel?: string;
  readonly formation: readonly FormationToken[];
  readonly lever: readonly LeverToken[];
  readonly reactionSpeed: ReactionSpeed;
  readonly owner: OwnerRole;
  /** Канонический utm_medium. Отсутствует у каналов без UTM (напр. прямые заходы). */
  readonly medium?: UtmMedium;
  readonly side: FunnelSide;
  /** Реф-канал: ссылка ведёт на воронковую страницу (REF_ → user_id реферера). */
  readonly isReferral?: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// LANDINGS — посадочные (PG_ воронковые / LST_ транзакционные)
// ─────────────────────────────────────────────────────────────────────────────

export type LandingKind = 'funnel' | 'transactional';

export interface Landing extends BaseEntity {
  readonly kind: 'landing';
  readonly layer: 'landings';
  readonly landingKind: LandingKind;
  /** Целевое действие: код события EVT_/заказа ORDER_ (id узла flow-step). */
  readonly targetEventId: ID;
  /** Следующий шаг воронки (человекочитаемо). */
  readonly nextStep: string;
  /** Конверсионная цель (короткая формулировка). */
  readonly conversionGoal: string;
  /** Для LST_ — привязка к рынку в шаблоне ключа. */
  readonly marketScoped?: boolean;
  /** Только тёплый/горячий трафик (например, LST_DIAG_*). */
  readonly warmOnly?: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// PLATFORM — пользовательский поток (события EVT_/заказы ORDER_)
// ─────────────────────────────────────────────────────────────────────────────

export type FlowStepKind = 'action' | 'event' | 'order' | 'grant';

export interface FlowStep extends BaseEntity {
  readonly kind: 'flow_step';
  readonly layer: 'platform';
  readonly stepKind: FlowStepKind;
  /** Порядок в сквозной цепочке (для авто-раскладки и связей). */
  readonly order: number;
  readonly iconKey: string;
  /** Код события/заказа (EVT_ или ORDER_), если применимо. */
  readonly eventCode?: string;
  /** Где хранится факт. */
  readonly storedIn: string;
  /** Источник данных. */
  readonly dataSource: string;
  readonly owner: OwnerRole;
  /** Входит в основную линейную цепочку (рёбра flow_next по возрастанию order). */
  readonly mainChain?: boolean;
  /** Куда вливается вне-линейное событие (id шагов цепочки). */
  readonly feedsInto?: readonly ID[];
  /** В какие узлы аналитики отдаётся факт (id узлов analytics). */
  readonly emitsTo?: readonly ID[];
}

// ─────────────────────────────────────────────────────────────────────────────
// ANALYTICS — поток данных (аналитический контур)
// ─────────────────────────────────────────────────────────────────────────────

export type AnalyticsNodeKind =
  | 'ad_platform'
  | 'web_analytics'
  | 'platform'
  | 'warehouse'
  | 'dashboard'
  | 'decision_engine';

export interface AnalyticsNode extends BaseEntity {
  readonly kind: 'analytics_node';
  readonly layer: 'analytics';
  readonly nodeKind: AnalyticsNodeKind;
  readonly order: number;
  readonly iconKey: string;
  /** Что здесь измеряется/хранится. */
  readonly holds: string;
  /** Пробел контура: данные пока не собираются автоматически. */
  readonly gap?: string;
  /** Подпись исходящего ребра к следующему узлу контура. */
  readonly flowLabel?: string;
  /** Куда контур передаёт управление (id метрик слоя decisions). */
  readonly feedsInto?: readonly ID[];
}

// ─────────────────────────────────────────────────────────────────────────────
// METRIC — измеримый показатель с порогами (светофор)
// ─────────────────────────────────────────────────────────────────────────────

export interface Threshold {
  readonly green: string;
  readonly yellow: string;
  readonly red: string;
}

export interface Metric extends BaseEntity {
  readonly kind: 'metric';
  readonly layer: 'decisions';
  readonly dataSource: string;
  readonly thresholds: Threshold;
  readonly unit?: string;
  /** Что показатель проверяет (столбец «Решение» таблицы Д.1). */
  readonly checks: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// DECISION — узел дерева решений (метрика → порог → решение → действие)
// ─────────────────────────────────────────────────────────────────────────────

export type DecisionTrigger = 'below' | 'above' | 'green' | 'red' | 'yellow' | 'benchmark';
export type ActionKind = 'fix_creative' | 'fix_landing' | 'scale' | 'stop' | 'pause' | 'review_product' | 'monitor';

export interface Decision extends BaseEntity {
  readonly kind: 'decision';
  readonly layer: 'decisions';
  /** Метрика-триггер. */
  readonly metricId: ID;
  readonly trigger: DecisionTrigger;
  /** Короткая формулировка условия («CTR ↓», «ДРР ≤ зелёный + объём»). */
  readonly condition: string;
  /** Действие. */
  readonly action: ActionKind;
  readonly actionLabel: string;
  /** Ставка на непроверенную гипотезу скрининга. */
  readonly hypothesis?: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// CELL — центральный объект: измерительная ячейка (источник × посадочная × рынок × вариант)
// ─────────────────────────────────────────────────────────────────────────────

export interface Cell extends BaseEntity {
  readonly kind: 'cell';
  readonly layer: 'cell';
  readonly market: Market;
  readonly language: Language;
  /** Канал (id источника MK_). */
  readonly channelId: ID;
  /** Посадочная (id PG_/LST_). */
  readonly landingId: ID;
  readonly audience: string;
  readonly creative: string;
  /** Бюджет ячейки, USD (правило: не менее $400). */
  readonly budgetUsd: number;
  readonly owner: OwnerRole;
  readonly status: CellStatus;
  /** Собранный utm_campaign = код ячейки. */
  readonly utmCampaign: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// RULE — допустимые/запрещённые связи источник → посадочная (матрица В)
// ─────────────────────────────────────────────────────────────────────────────

export interface Rule extends BaseEntity {
  readonly kind: 'rule';
  readonly layer: 'landings';
  readonly sourceIds: readonly ID[];
  readonly temperature: Temperature;
  readonly temperatureLabel?: string;
  /** Основная посадочная (id). */
  readonly primaryLandingId: ID;
  /** Допустимые посадочные (id). */
  readonly allowedLandingIds: readonly ID[];
  readonly targetAction: string;
  /** Запрещённые связи с причиной. */
  readonly forbidden: readonly ForbiddenLink[];
}

export interface ForbiddenLink {
  /** id посадочной (или спец-ключ паттерна, напр. любой LST_DIAG_*). */
  readonly landingId: ID;
  readonly reason: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// CONTRACTOR — шаблон запуска подрядчику (блок Д.3)
// ─────────────────────────────────────────────────────────────────────────────

export interface ContractorField {
  readonly key: string;
  readonly label: string;
  readonly value: string;
  readonly note?: string;
}

export interface ContractorTemplate extends BaseEntity {
  readonly kind: 'contractor';
  readonly layer: 'contractor';
  readonly fields: readonly ContractorField[];
  readonly prohibitions: readonly string[];
  readonly reporting: string;
  readonly stopRule: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// LAYER — архитектурный слой (метаданные для раскладки и сворачивания)
// ─────────────────────────────────────────────────────────────────────────────

export interface LayerDef {
  readonly id: LayerId;
  readonly order: number;
  readonly title: string;
  readonly subtitle: string;
  readonly kinds: readonly EntityKind[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Объединение сущностей
// ─────────────────────────────────────────────────────────────────────────────

export type DomainEntity =
  | TrafficSource
  | Landing
  | FlowStep
  | AnalyticsNode
  | Metric
  | Decision
  | Cell
  | ContractorTemplate;

/** Всё, что может быть выбрано и показано в инспекторе (включая правила). */
export type Inspectable = DomainEntity | Rule;
