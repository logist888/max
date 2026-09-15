import type { Cell } from '@/types';

/**
 * Слой CELL — измерительные ячейки (центральный объект системы).
 * CELL = источник × посадочная × рынок × вариант. Минимальная единица теста, бюджета (≥ $400),
 * UTM-кампании и решения. utmCampaign = код ячейки («одна кампания — одна посадочная»).
 * Ниже — примерный набор [ОЦЕНКА] для демонстрации; реальные ячейки заводятся так же — только данными.
 * Источник структуры: docs/12-traffic-platform-decisions.md, блок Г.1 + раздел CELL.
 */
export const CELLS: readonly Cell[] = [
  {
    id: 'cell_vk_quiz_ru_01', kind: 'cell', layer: 'cell', code: 'CELL_VK_QUIZ_RU_01', name: 'VK · Квиз · RU · 01',
    market: 'CIS', language: 'RU', channelId: 'mk_vk_ads', landingId: 'pg_quiz',
    audience: 'Родители 35–45, СНГ, интерес к будущему ребёнка', creative: 'Оцифровка тревоги за будущее ребёнка',
    budgetUsd: 400, owner: 'marketing_lead', status: 'active', utmCampaign: 'CELL_VK_QUIZ_RU_01', confidence: 'estimate',
  },
  {
    id: 'cell_meta_quiz_en_01', kind: 'cell', layer: 'cell', code: 'CELL_META_QUIZ_EN_01', name: 'Meta · Квиз · EN · 01',
    market: 'MENA', language: 'EN', channelId: 'mk_meta_ads', landingId: 'pg_quiz',
    audience: 'Экспаты MENA, EN-говорящие родители', creative: 'Career screening for teens',
    budgetUsd: 500, owner: 'marketing_lead', status: 'active', utmCampaign: 'CELL_META_QUIZ_EN_01', confidence: 'estimate',
  },
  {
    id: 'cell_meta_quiz_ar_01', kind: 'cell', layer: 'cell', code: 'CELL_META_QUIZ_AR_01', name: 'Meta · Квиз · AR · 01',
    market: 'MENA', language: 'AR', channelId: 'mk_meta_ads', landingId: 'pg_quiz',
    audience: 'Арабоязычные родители Персидского залива', creative: 'تشخيص ميول المراهق المهنية',
    budgetUsd: 450, owner: 'marketing_lead', status: 'scaling', utmCampaign: 'CELL_META_QUIZ_AR_01', confidence: 'estimate',
  },
  {
    id: 'cell_ya_quiz_ru_02', kind: 'cell', layer: 'cell', code: 'CELL_YA_QUIZ_RU_02', name: 'Яндекс · Квиз · RU · 02',
    market: 'CIS', language: 'RU', channelId: 'mk_ya_direct', landingId: 'pg_quiz',
    audience: 'Инфо-запросы «кем стать подростку», СНГ', creative: 'Тест на профориентацию за 15 минут',
    budgetUsd: 400, owner: 'marketing_lead', status: 'paused', utmCampaign: 'CELL_YA_QUIZ_RU_02', confidence: 'estimate',
  },
  {
    id: 'cell_tg_quiz_ru_01', kind: 'cell', layer: 'cell', code: 'CELL_TG_QUIZ_RU_01', name: 'TG-посев · Квиз · RU · 01',
    market: 'CIS', language: 'RU', channelId: 'mk_tg_seed', landingId: 'pg_quiz',
    audience: 'Родительские Telegram-каналы, СНГ', creative: 'Пост-рекомендация в канале о воспитании',
    budgetUsd: 400, owner: 'marketing_lead', status: 'active', utmCampaign: 'CELL_TG_QUIZ_RU_01', confidence: 'estimate',
  },
  {
    id: 'cell_rmkt_diag_ru_01', kind: 'cell', layer: 'cell', code: 'CELL_RMKT_DIAG_RU_01', name: 'Ремаркетинг · Карточка · RU · 01',
    market: 'CIS', language: 'RU', channelId: 'mk_remarketing', landingId: 'lst_diag',
    audience: 'Прошли квиз, не купили (по пикселю)', creative: 'Полная диагностика — раскрой сильные стороны',
    budgetUsd: 400, owner: 'marketing_lead', status: 'scaling', utmCampaign: 'CELL_RMKT_DIAG_RU_01', confidence: 'estimate',
  },
  {
    id: 'cell_email_p10_ru_01', kind: 'cell', layer: 'cell', code: 'CELL_EMAIL_P10_RU_01', name: 'Email · Профиль 10 · RU · 01',
    market: 'CIS', language: 'RU', channelId: 'mk_email', landingId: 'pg_profile10',
    audience: 'База зарегистрированных, Профиль 10 не активирован', creative: 'Допройди профиль — открой рекомендации',
    budgetUsd: 400, owner: 'crm_lead', status: 'active', utmCampaign: 'CELL_EMAIL_P10_RU_01', confidence: 'estimate',
  },
  {
    id: 'cell_google_quiz_en_01', kind: 'cell', layer: 'cell', code: 'CELL_GOOGLE_QUIZ_EN_01', name: 'Google · Квиз · EN · 01',
    market: 'MENA', language: 'EN', channelId: 'mk_google_ads', landingId: 'pg_quiz',
    audience: 'Инфо-запросы MENA, EN', creative: 'What career fits your teen?',
    budgetUsd: 400, owner: 'marketing_lead', status: 'stopped', utmCampaign: 'CELL_GOOGLE_QUIZ_EN_01', confidence: 'estimate',
  },
  {
    id: 'cell_webinar_web_ru_01', kind: 'cell', layer: 'cell', code: 'CELL_WEBINAR_WEB_RU_01', name: 'Вебинар · Регистрация · RU · 01',
    market: 'CIS', language: 'RU', channelId: 'mk_webinar', landingId: 'pg_webinar',
    audience: 'Прогрев к первому вебинару, СНГ', creative: 'Бесплатный вебинар: профориентация без ошибок',
    budgetUsd: 400, owner: 'crm_lead', status: 'active', utmCampaign: 'CELL_WEBINAR_WEB_RU_01', confidence: 'estimate',
  },
  {
    id: 'cell_ref_quiz_ru_01', kind: 'cell', layer: 'cell', code: 'CELL_REF_QUIZ_RU_01', name: 'Реферал · Квиз · RU · 01',
    market: 'CIS', language: 'RU', channelId: 'mk_ref_user', landingId: 'pg_quiz',
    audience: 'Рефералы от прошедших диагностику', creative: 'Друг рекомендует: пройди скрининг',
    budgetUsd: 400, owner: 'partner_lead', status: 'draft', utmCampaign: 'CELL_REF_QUIZ_RU_01', confidence: 'estimate',
  },
];
