import type { Rule } from '@/types';

/**
 * Матрица соответствия «источник → посадочная → действие → запрет» (блок В).
 * Логика: температура трафика × чек. Холодный трафик → воронковые (квалификация до цены);
 * тёплый — ближе к заказу; горячий — карточка. Инвариант: холодный трафик на LST_DIAG_* — никогда.
 * forbidden → красные пунктирные рёбра с причиной. Источник: docs/12, блок В.
 */
export const RULES: readonly Rule[] = [
  {
    id: 'rule_01', kind: 'rule', layer: 'landings', code: 'RULE_01', name: 'VK / Meta (холод) → квиз',
    description: 'Платный холодный аукцион ведём в квалификацию, не на карточку.',
    sourceIds: ['mk_vk_ads', 'mk_meta_ads'], temperature: 'cold',
    primaryLandingId: 'pg_quiz', allowedLandingIds: ['pg_webinar', 'pg_blog'],
    targetAction: 'EVT_SCREENING_DONE / EVT_REG',
    forbidden: [
      { landingId: 'lst_diag', reason: 'холод + высокий чек = слив бюджета' },
      { landingId: 'pg_home', reason: 'нет одного измеримого действия' },
    ],
  },
  {
    id: 'rule_02', kind: 'rule', layer: 'landings', code: 'RULE_02', name: 'Контекст (инфо) → квиз',
    description: 'Инфо-запросы Яндекс/Google — холод, в квиз.',
    sourceIds: ['mk_ya_direct', 'mk_google_ads'], temperature: 'cold',
    primaryLandingId: 'pg_quiz', allowedLandingIds: ['pg_blog', 'pg_category'],
    targetAction: 'EVT_SCREENING_DONE',
    forbidden: [
      { landingId: 'lst_diag', reason: 'холодный трафик на карточку запрещён' },
      { landingId: 'pg_home', reason: 'нет одного измеримого действия' },
    ],
  },
  {
    id: 'rule_03', kind: 'rule', layer: 'landings', code: 'RULE_03', name: 'Контекст (бренд/коммерч.) → тёплый',
    description: 'Бренд/коммерческий запрос — тёплый; можно к карточке при явном бренд-спросе.',
    sourceIds: ['mk_ya_direct', 'mk_google_ads'], temperature: 'warm',
    primaryLandingId: 'pg_category', allowedLandingIds: ['pg_home', 'lst_diag'],
    targetAction: 'EVT_GOTO_QUIZ / ORDER_DIAG',
    forbidden: [],
  },
  {
    id: 'rule_04', kind: 'rule', layer: 'landings', code: 'RULE_04', name: 'Посевы / блогеры (холод) → квиз',
    description: 'TG-посевы и блогеры — рекомендательный холод, в квиз.',
    sourceIds: ['mk_tg_seed', 'mk_blog_paid', 'mk_blog_org'], temperature: 'cold',
    primaryLandingId: 'pg_quiz', allowedLandingIds: ['pg_webinar'],
    targetAction: 'EVT_SCREENING_DONE',
    forbidden: [
      { landingId: 'lst_diag', reason: 'холодный трафик на карточку запрещён' },
      { landingId: 'pg_home', reason: 'нет одного измеримого действия' },
    ],
  },
  {
    id: 'rule_05', kind: 'rule', layer: 'landings', code: 'RULE_05', name: 'Видео / свои соцсети → квиз',
    description: 'Видео и органика соцсетей — холод–тёпл, основной путь в квиз.',
    sourceIds: ['mk_video', 'mk_own_social_ru', 'mk_own_social_en'], temperature: 'cold', temperatureLabel: 'холод–тёпл',
    primaryLandingId: 'pg_quiz', allowedLandingIds: ['pg_webinar', 'pg_blog'],
    targetAction: 'EVT_SCREENING_DONE',
    forbidden: [{ landingId: 'lst_diag', reason: 'карточка запрещена для холодной части трафика' }],
  },
  {
    id: 'rule_06', kind: 'rule', layer: 'landings', code: 'RULE_06', name: 'SEO инфо → блог',
    description: 'Информационная выдача — холод, целевое действие переход в квиз.',
    sourceIds: ['mk_seo_info'], temperature: 'cold',
    primaryLandingId: 'pg_blog', allowedLandingIds: ['pg_quiz'],
    targetAction: 'EVT_GOTO_QUIZ',
    forbidden: [{ landingId: 'lst_diag', reason: 'холодный трафик на карточку запрещён' }],
  },
  {
    id: 'rule_07', kind: 'rule', layer: 'landings', code: 'RULE_07', name: 'SEO коммерч. → категория',
    description: 'Коммерческая выдача — тёплый, можно к карточке.',
    sourceIds: ['mk_seo_comm'], temperature: 'warm',
    primaryLandingId: 'pg_category', allowedLandingIds: ['pg_quiz', 'lst_diag'],
    targetAction: 'EVT_GOTO_QUIZ / ORDER_DIAG',
    forbidden: [],
  },
  {
    id: 'rule_08', kind: 'rule', layer: 'landings', code: 'RULE_08', name: 'SEO бренд / прямые → главная',
    description: 'Брендовый и прямой спрос — тёпл–горячий, главная и карточка.',
    sourceIds: ['mk_seo_brand', 'mk_direct'], temperature: 'warm', temperatureLabel: 'тёпл–гор',
    primaryLandingId: 'pg_home', allowedLandingIds: ['lst_diag', 'pg_profile10'],
    targetAction: 'ORDER_DIAG / повторный вход',
    forbidden: [],
  },
  {
    id: 'rule_09', kind: 'rule', layer: 'landings', code: 'RULE_09', name: 'PR → главная / блог',
    description: 'PR — репутационный формат, без прямого призыва к покупке.',
    sourceIds: ['mk_pr'], temperature: 'cold',
    primaryLandingId: 'pg_blog', allowedLandingIds: ['pg_home', 'pg_quiz'],
    targetAction: 'EVT_GOTO_QUIZ',
    forbidden: [{ landingId: 'lst_diag', reason: 'прямой призыв к покупке ломает репутационный формат' }],
  },
  {
    id: 'rule_10', kind: 'rule', layer: 'landings', code: 'RULE_10', name: 'Email / рассылки → Профиль 10 / карточка',
    description: 'Тёплая база — к активации Профиля 10 и карточке.',
    sourceIds: ['mk_email', 'mk_msg_broadcast'], temperature: 'warm', temperatureLabel: 'тёпл (база)',
    primaryLandingId: 'pg_profile10', allowedLandingIds: ['lst_diag', 'pg_webinar'],
    targetAction: 'ORDER_DIAG / EVT_WEBINAR_REG',
    forbidden: [{ landingId: 'pg_quiz', reason: 'повторный квиз для прошедших — лишний шаг' }],
  },
  {
    id: 'rule_11', kind: 'rule', layer: 'landings', code: 'RULE_11', name: 'Ремаркетинг → карточка',
    description: 'Горячий трафик по пикселю/базе — прямо на карточку.',
    sourceIds: ['mk_remarketing'], temperature: 'hot',
    primaryLandingId: 'lst_diag', allowedLandingIds: ['pg_profile10'],
    targetAction: 'ORDER_DIAG',
    forbidden: [{ landingId: 'pg_home', reason: 'главная размывает намерение горячего трафика' }],
  },
  {
    id: 'rule_12', kind: 'rule', layer: 'landings', code: 'RULE_12', name: 'Рефералы → квиз',
    description: 'Реф-трафик — тёплый; в UTM обязателен ref_id.',
    sourceIds: ['mk_ref_user'], temperature: 'warm',
    primaryLandingId: 'pg_quiz', allowedLandingIds: ['lst_diag'],
    targetAction: 'EVT_SCREENING_DONE / ORDER_DIAG',
    forbidden: [],
  },
  {
    id: 'rule_13', kind: 'rule', layer: 'landings', code: 'RULE_13', name: 'Партнёрства → квиз',
    description: 'Школы и репетиторы — тёплый, квиз или со-брендированная категория.',
    sourceIds: ['mk_partner_edu'], temperature: 'warm',
    primaryLandingId: 'pg_quiz', allowedLandingIds: ['pg_category', 'pg_webinar'],
    targetAction: 'EVT_SCREENING_DONE',
    forbidden: [{ landingId: 'pg_home', reason: 'нет одного измеримого действия' }],
  },
  {
    id: 'rule_14', kind: 'rule', layer: 'landings', code: 'RULE_14', name: 'Вебинар → регистрация',
    description: 'Прогрев: регистрация на вебинар, карточка — только после эфира.',
    sourceIds: ['mk_webinar'], temperature: 'nurture',
    primaryLandingId: 'pg_webinar', allowedLandingIds: ['pg_quiz'],
    targetAction: 'EVT_WEBINAR_REG → ORDER_DIAG',
    forbidden: [{ landingId: 'lst_diag', reason: 'холодная карточка до эфира — только после вебинара' }],
  },
];
