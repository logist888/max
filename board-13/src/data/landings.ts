import type { Landing } from '@/types';

/**
 * Блок Б — реестр посадочных (PG_ воронковые / LST_ транзакционные).
 * targetEventId ссылается на шаг платформы (события EVT_ / заказы ORDER_).
 * Источник: docs/12-traffic-platform-decisions.md, блок Б.
 */
export const LANDINGS: readonly Landing[] = [
  {
    id: 'pg_quiz', kind: 'landing', layer: 'landings', code: 'PG_QUIZ', name: 'Квиз (скрининг)',
    description: 'Воронковая: холодный трафик проходит квалификацию до цены. При вводе e-mail — регистрация.',
    landingKind: 'funnel', targetEventId: 'flow_screening', nextStep: 'Профиль 10',
    conversionGoal: 'EVT_SCREENING_DONE (+ EVT_REG при e-mail)',
  },
  {
    id: 'pg_profile10', kind: 'landing', layer: 'landings', code: 'PG_PROFILE10', name: 'Профиль 10 (ЛК)',
    description: 'Воронковая: freemium-профиль в личном кабинете. Заполнение → апселл на диагностику.',
    landingKind: 'funnel', targetEventId: 'flow_activation', nextStep: 'покупка диагностики',
    conversionGoal: 'EVT_PROFILE10_ACTIVATED',
  },
  {
    id: 'pg_webinar', kind: 'landing', layer: 'landings', code: 'PG_WEBINAR', name: 'Вебинар (регистрация)',
    description: 'Воронковая: регистрация на вебинар как параллельный прогрев. После эфира — карточка.',
    landingKind: 'funnel', targetEventId: 'evt_webinar_reg', nextStep: 'прогрев → квиз / диагностика',
    conversionGoal: 'EVT_WEBINAR_REG',
  },
  {
    id: 'pg_home', kind: 'landing', layer: 'landings', code: 'PG_HOME', name: 'Главная',
    description: 'Воронковая: только для брендового / прямого / PR-трафика. НЕ бывает основной посадочной платного холодного трафика.',
    landingKind: 'funnel', targetEventId: 'evt_goto_quiz', nextStep: 'квиз',
    conversionGoal: 'EVT_GOTO_QUIZ (переход в квиз)',
  },
  {
    id: 'pg_category', kind: 'landing', layer: 'landings', code: 'PG_CATEGORY', name: 'Категория',
    description: 'Воронковая: страница категории. Для холода — в квиз, для тёплых — к карточке.',
    landingKind: 'funnel', targetEventId: 'evt_goto_quiz', nextStep: 'квиз / карточка (для тёплых)',
    conversionGoal: 'EVT_GOTO_QUIZ / EVT_VIEW_LISTING',
  },
  {
    id: 'pg_blog', kind: 'landing', layer: 'landings', code: 'PG_BLOG', name: 'Блог / статья',
    description: 'Воронковая: информационная статья. Целевое действие — переход в квиз.',
    landingKind: 'funnel', targetEventId: 'evt_goto_quiz', nextStep: 'квиз',
    conversionGoal: 'EVT_GOTO_QUIZ',
  },
  {
    id: 'lst_diag', kind: 'landing', layer: 'landings', code: 'LST_DIAG_<market>', name: 'Карточка диагностики',
    description: 'Транзакционная (SKU × канал × рынок). Только тёплый/горячий трафик. Холодный трафик запрещён (чек 50 000 ₽).',
    landingKind: 'transactional', targetEventId: 'flow_order_diag', nextStep: 'членство (в подарок)',
    conversionGoal: 'ORDER_DIAG (покупка 50К)', marketScoped: true, warmOnly: true,
  },
  {
    id: 'lst_renew', kind: 'landing', layer: 'landings', code: 'LST_RENEW_<market>', name: 'Карточка продления',
    description: 'Транзакционная: продление членства. Работает на удержание тёплой базы.',
    landingKind: 'transactional', targetEventId: 'flow_renewal', nextStep: 'удержание',
    conversionGoal: 'ORDER_RENEW (продление членства)', marketScoped: true, warmOnly: true,
  },
];
