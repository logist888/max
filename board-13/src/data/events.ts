import type { FlowStep } from '@/types';

/**
 * Слой PLATFORM — пользовательский поток и сквозная цепочка (блоки Б, Г.2 + раздел PLATFORM).
 * Основная линейная цепочка (mainChain) — рёбра flow_next по возрастанию order.
 * Вне-линейные события (evt_goto_quiz, evt_webinar_reg, evt_view_listing) вливаются через feedsInto.
 * emitsTo — куда факт отдаётся в учётный контур (слой ANALYTICS).
 * Источник: docs/12-traffic-platform-decisions.md, разделы Б, Г.2.
 */
export const FLOW_STEPS: readonly FlowStep[] = [
  {
    id: 'flow_click', kind: 'flow_step', layer: 'platform', code: 'CLICK', name: 'Клик',
    description: 'Клик по объявлению. Фиксируется client_id, UTM/ref_id.',
    stepKind: 'action', order: 1, iconKey: 'cursor', storedIn: 'Метрика / GA (пиксель)',
    dataSource: 'рекламный кабинет', owner: 'marketing_lead', mainChain: true, emitsTo: ['an_web_analytics'],
  },
  {
    id: 'flow_landing', kind: 'flow_step', layer: 'platform', code: 'LANDING', name: 'Посадочная',
    description: 'Пользователь на посадочной. Событие посадочной EVT_<landing>.',
    stepKind: 'event', order: 2, iconKey: 'file', eventCode: 'EVT_<landing>',
    storedIn: 'Метрика / платформа', dataSource: 'Метрика', owner: 'marketing_lead', mainChain: true, emitsTo: ['an_web_analytics'],
  },
  {
    id: 'flow_screening', kind: 'flow_step', layer: 'platform', code: 'EVT_SCREENING_DONE', name: 'Скрининг пройден',
    description: 'Прохождение квиза. Целевое действие холодного трафика.',
    stepKind: 'event', order: 3, iconKey: 'clipboardCheck', eventCode: 'EVT_SCREENING_DONE',
    storedIn: 'платформа (append-only)', dataSource: 'Метрика / платформа', owner: 'marketing_lead', mainChain: true, emitsTo: ['an_web_analytics'],
  },
  {
    id: 'flow_profile10', kind: 'flow_step', layer: 'platform', code: 'PROFILE10', name: 'Профиль 10',
    description: 'Freemium-профиль показан. Дальше — активация и апселл.',
    stepKind: 'action', order: 4, iconKey: 'file', storedIn: 'платформа',
    dataSource: 'платформа', owner: 'marketing_lead', mainChain: true,
  },
  {
    id: 'flow_registration', kind: 'flow_step', layer: 'platform', code: 'EVT_REG', name: 'Регистрация',
    description: 'Создан user_id. Точка сшивки: client_id/ym:uid → user_id, UTM/ref_id пишутся в атрибуцию.',
    stepKind: 'event', order: 5, iconKey: 'userPlus', eventCode: 'EVT_REG',
    storedIn: 'платформа (Rust)', dataSource: 'стык Метрика ↔ платформа', owner: 'marketing_lead', mainChain: true, emitsTo: ['an_platform'],
  },
  {
    id: 'flow_activation', kind: 'flow_step', layer: 'platform', code: 'EVT_PROFILE10_ACTIVATED', name: 'Активация',
    description: 'Профиль 10 активирован (заполнен).',
    stepKind: 'event', order: 6, iconKey: 'userCheck', eventCode: 'EVT_PROFILE10_ACTIVATED',
    storedIn: 'платформа (append-only)', dataSource: 'платформа', owner: 'marketing_lead', mainChain: true, emitsTo: ['an_platform'],
  },
  {
    id: 'flow_order_diag', kind: 'flow_step', layer: 'platform', code: 'ORDER_DIAG', name: 'Заказ диагностики',
    description: 'Заказ диагностики (50 000 ₽). Центральная ставка гипотезы скрининга.',
    stepKind: 'order', order: 7, iconKey: 'cart', eventCode: 'ORDER_DIAG',
    storedIn: 'платформа (append-only)', dataSource: 'платформа', owner: 'marketing_lead', mainChain: true, emitsTo: ['an_platform'],
  },
  {
    id: 'flow_payment', kind: 'flow_step', layer: 'platform', code: 'PAYMENT', name: 'Оплата',
    description: 'Оплата заказа диагностики. Формирует выручку канала для ДРР.',
    stepKind: 'order', order: 8, iconKey: 'card', storedIn: 'платёжный провайдер / платформа',
    dataSource: 'платформа', owner: 'marketing_lead', mainChain: true, emitsTo: ['an_platform'],
  },
  {
    id: 'flow_membership', kind: 'flow_step', layer: 'platform', code: 'MEMBERSHIP', name: 'Членство',
    description: 'Членство выдаётся в подарок к диагностике (grant).',
    stepKind: 'grant', order: 9, iconKey: 'award', storedIn: 'платформа',
    dataSource: 'платформа', owner: 'crm_lead', mainChain: true, emitsTo: ['an_platform'],
  },
  {
    id: 'flow_renewal', kind: 'flow_step', layer: 'platform', code: 'ORDER_RENEW', name: 'Продление',
    description: 'Продление членства. Работает на удержание и LTV.',
    stepKind: 'order', order: 10, iconKey: 'repeat', eventCode: 'ORDER_RENEW',
    storedIn: 'платформа (append-only)', dataSource: 'платформа', owner: 'crm_lead', mainChain: true, emitsTo: ['an_platform'],
  },

  // — вне-линейные события (не в основной цепочке) —
  {
    id: 'evt_goto_quiz', kind: 'flow_step', layer: 'platform', code: 'EVT_GOTO_QUIZ', name: 'Переход в квиз',
    description: 'Целевое действие главной / категории / блога: переход в квиз.',
    stepKind: 'event', order: 3, iconKey: 'cursor', eventCode: 'EVT_GOTO_QUIZ',
    storedIn: 'Метрика / платформа', dataSource: 'Метрика', owner: 'content_lead', feedsInto: ['flow_screening'], emitsTo: ['an_web_analytics'],
  },
  {
    id: 'evt_webinar_reg', kind: 'flow_step', layer: 'platform', code: 'EVT_WEBINAR_REG', name: 'Регистрация на вебинар',
    description: 'Целевое действие вебинарной посадочной. После эфира — карточка диагностики.',
    stepKind: 'event', order: 4, iconKey: 'presentation', eventCode: 'EVT_WEBINAR_REG',
    storedIn: 'платформа / CRM', dataSource: 'платформа', owner: 'crm_lead', feedsInto: ['flow_order_diag'], emitsTo: ['an_platform'],
  },
  {
    id: 'evt_view_listing', kind: 'flow_step', layer: 'platform', code: 'EVT_VIEW_LISTING', name: 'Просмотр карточки',
    description: 'Тёплый пользователь на карточке. Ведёт к заказу диагностики.',
    stepKind: 'event', order: 6, iconKey: 'file', eventCode: 'EVT_VIEW_LISTING',
    storedIn: 'Метрика / платформа', dataSource: 'Метрика', owner: 'marketing_lead', feedsInto: ['flow_order_diag'], emitsTo: ['an_web_analytics'],
  },
];
