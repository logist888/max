import type { TrafficSource } from '@/types';

/**
 * Блок А — реестр источников трафика (закрытый словарь MK_).
 * Новый канал добавляется сюда, а не заводится ad hoc. Температура — репрезентативная
 * (из матрицы В); диапазоны сохранены в temperatureLabel. Владельцы — по каденции Д.2.
 * Источник: docs/12-traffic-platform-decisions.md, блок А.
 */
export const TRAFFIC_SOURCES: readonly TrafficSource[] = [
  {
    id: 'mk_vk_ads', kind: 'traffic_source', layer: 'traffic', code: 'MK_VK_ADS',
    name: 'Таргет VK', description: 'Аукционный таргет во ВКонтакте, рынок СНГ. Холодный трафик в квалификацию.',
    market: 'CIS', temperature: 'cold', formation: ['auction'], lever: ['budget'],
    reactionSpeed: 'hours', owner: 'marketing_lead', medium: 'cpc', side: 'family',
  },
  {
    id: 'mk_meta_ads', kind: 'traffic_source', layer: 'traffic', code: 'MK_META_ADS',
    name: 'Таргет Meta', description: 'Аукционный таргет Meta, преимущественно MENA и диаспора (в СНГ ограничен).',
    market: 'MENA', temperature: 'cold', formation: ['auction'], lever: ['budget'],
    reactionSpeed: 'hours', owner: 'marketing_lead', medium: 'cpc', side: 'family',
  },
  {
    id: 'mk_ya_direct', kind: 'traffic_source', layer: 'traffic', code: 'MK_YA_DIRECT',
    name: 'Контекст Яндекс', description: 'Контекстная реклама Яндекс.Директ, СНГ. Инфо-запросы — холод, бренд/коммерч. — тёплый.',
    market: 'CIS', temperature: 'cold', temperatureLabel: 'холод / тёпл (бренд)',
    formation: ['auction'], lever: ['budget'], reactionSpeed: 'hours', owner: 'marketing_lead', medium: 'cpc', side: 'family',
  },
  {
    id: 'mk_google_ads', kind: 'traffic_source', layer: 'traffic', code: 'MK_GOOGLE_ADS',
    name: 'Контекст Google', description: 'Контекст Google, MENA и оба рынка. Инфо-запросы — холод, бренд — тёплый.',
    market: 'BOTH', temperature: 'cold', temperatureLabel: 'холод / тёпл (бренд)',
    formation: ['auction'], lever: ['budget'], reactionSpeed: 'hours', owner: 'marketing_lead', medium: 'cpc', side: 'family',
  },
  {
    id: 'mk_tg_seed', kind: 'traffic_source', layer: 'traffic', code: 'MK_TG_SEED',
    name: 'Посевы в Telegram', description: 'Рекомендательные посты в Telegram-каналах. Отклик — часы после поста.',
    market: 'BOTH', temperature: 'cold', formation: ['recommendation'], lever: ['relations', 'budget'],
    reactionSpeed: 'hours', owner: 'marketing_lead', medium: 'social', side: 'family',
  },
  {
    id: 'mk_blog_paid', kind: 'traffic_source', layer: 'traffic', code: 'MK_BLOG_PAID',
    name: 'Блогеры платные', description: 'Платные размещения у блогеров. Рекомендательный формат, отклик — недели.',
    market: 'BOTH', temperature: 'cold', formation: ['recommendation'], lever: ['budget', 'relations'],
    reactionSpeed: 'weeks', owner: 'partner_lead', medium: 'affiliate', side: 'family',
  },
  {
    id: 'mk_blog_org', kind: 'traffic_source', layer: 'traffic', code: 'MK_BLOG_ORG',
    name: 'Блогеры нативные', description: 'Нативные упоминания без прямой оплаты. Держится на отношениях и контенте.',
    market: 'BOTH', temperature: 'cold', formation: ['recommendation'], lever: ['relations', 'content'],
    reactionSpeed: 'weeks_months', owner: 'content_lead', medium: 'referral', side: 'family',
  },
  {
    id: 'mk_own_social_ru', kind: 'traffic_source', layer: 'traffic', code: 'MK_OWN_SOCIAL_RU',
    name: 'Свои соцсети RU', description: 'Органика собственных RU-соцсетей. Рычаг — контент.',
    market: 'CIS', temperature: 'cold', temperatureLabel: 'холод–тёпл',
    formation: ['recommendation', 'search'], lever: ['content'], reactionSpeed: 'weeks_months', owner: 'content_lead', medium: 'social', side: 'family',
  },
  {
    id: 'mk_own_social_en', kind: 'traffic_source', layer: 'traffic', code: 'MK_OWN_SOCIAL_EN',
    name: 'Свои соцсети EN', description: 'Органика собственных EN-соцсетей для MENA. Рычаг — контент.',
    market: 'MENA', temperature: 'cold', temperatureLabel: 'холод–тёпл',
    formation: ['recommendation', 'search'], lever: ['content'], reactionSpeed: 'weeks_months', owner: 'content_lead', medium: 'social', side: 'family',
  },
  {
    id: 'mk_video', kind: 'traffic_source', layer: 'traffic', code: 'MK_VIDEO',
    name: 'Видеоконтент', description: 'YouTube / Shorts / Reels. Выдача + рекомендация, отклик — недели-месяцы.',
    market: 'BOTH', temperature: 'cold', temperatureLabel: 'холод–тёпл',
    formation: ['search', 'recommendation'], lever: ['content'], reactionSpeed: 'weeks_months', owner: 'content_lead', medium: 'video', side: 'family',
  },
  {
    id: 'mk_seo_info', kind: 'traffic_source', layer: 'traffic', code: 'MK_SEO_INFO',
    name: 'SEO информационный', description: 'Информационная выдача. Холодный трафик, рычаг — контент + время.',
    market: 'BOTH', temperature: 'cold', formation: ['search'], lever: ['content', 'time'],
    reactionSpeed: 'months', owner: 'content_lead', medium: 'seo', side: 'family',
  },
  {
    id: 'mk_seo_comm', kind: 'traffic_source', layer: 'traffic', code: 'MK_SEO_COMM',
    name: 'SEO коммерческий', description: 'Коммерческая выдача. Тёплый трафик ближе к заказу.',
    market: 'BOTH', temperature: 'warm', formation: ['search'], lever: ['content', 'time'],
    reactionSpeed: 'months', owner: 'content_lead', medium: 'seo', side: 'family',
  },
  {
    id: 'mk_seo_brand', kind: 'traffic_source', layer: 'traffic', code: 'MK_SEO_BRAND',
    name: 'SEO брендовый', description: 'Брендовый спрос из выдачи. Тёпл–горячий, рычаг — время / бренд.',
    market: 'BOTH', temperature: 'warm', temperatureLabel: 'тёпл–гор',
    formation: ['search'], lever: ['time', 'brand'], reactionSpeed: 'months', owner: 'content_lead', medium: 'seo', side: 'family',
  },
  {
    id: 'mk_pr', kind: 'traffic_source', layer: 'traffic', code: 'MK_PR',
    name: 'PR', description: 'Рекомендация через медиа. Репутационный формат, без прямого призыва к покупке.',
    market: 'BOTH', temperature: 'cold', formation: ['recommendation'], lever: ['relations'],
    reactionSpeed: 'weeks_months', owner: 'partner_lead', medium: 'pr', side: 'family',
  },
  {
    id: 'mk_email', kind: 'traffic_source', layer: 'traffic', code: 'MK_EMAIL',
    name: 'Email', description: 'Рассылки по базе. Тёплый трафик, отклик — часы.',
    market: 'BOTH', temperature: 'warm', temperatureLabel: 'тёпл (база)',
    formation: ['base'], lever: ['content'], reactionSpeed: 'hours', owner: 'crm_lead', medium: 'email', side: 'family',
  },
  {
    id: 'mk_msg_broadcast', kind: 'traffic_source', layer: 'traffic', code: 'MK_MSG_BROADCAST',
    name: 'Мессенджер-рассылки', description: 'TG / WhatsApp-бот по базе. Тёплый трафик, отклик — часы.',
    market: 'BOTH', temperature: 'warm', temperatureLabel: 'тёпл (база)',
    formation: ['base'], lever: ['content'], reactionSpeed: 'hours', owner: 'crm_lead', medium: 'email', side: 'family',
  },
  {
    id: 'mk_remarketing', kind: 'traffic_source', layer: 'traffic', code: 'MK_REMARKETING',
    name: 'Ремаркетинг', description: 'Аукцион по пикселю / базе. Горячий трафик — ведём на карточку.',
    market: 'BOTH', temperature: 'hot', formation: ['auction', 'base'], lever: ['budget', 'base'],
    reactionSpeed: 'hours', owner: 'marketing_lead', medium: 'remarketing', side: 'family',
  },
  {
    id: 'mk_ref_user', kind: 'traffic_source', layer: 'traffic', code: 'MK_REF_USER',
    name: 'Реф-ссылки пользователей', description: 'Рекомендация через продукт. В UTM обязателен ref_id → user_id реферера.',
    market: 'BOTH', temperature: 'warm', formation: ['recommendation'], lever: ['relations'],
    reactionSpeed: 'weeks', owner: 'partner_lead', medium: 'referral', side: 'family', isReferral: true,
  },
  {
    id: 'mk_ref_expert', kind: 'traffic_source', layer: 'traffic', code: 'MK_REF_EXPERT',
    name: 'Реф-ссылки экспертов', description: 'Сторона экспертов. Метрики НЕ смешиваются с семейной воронкой.',
    market: 'BOTH', temperature: 'warm', formation: ['recommendation'], lever: ['relations'],
    reactionSpeed: 'weeks', owner: 'partner_lead', medium: 'referral', side: 'expert', isReferral: true,
  },
  {
    id: 'mk_partner_edu', kind: 'traffic_source', layer: 'traffic', code: 'MK_PARTNER_EDU',
    name: 'Партнёрства', description: 'Школы, репетиторы. База + отношения, часто со-брендированная посадочная.',
    market: 'BOTH', temperature: 'warm', formation: ['base'], lever: ['relations'],
    reactionSpeed: 'weeks_months', owner: 'partner_lead', medium: 'affiliate', side: 'family',
  },
  {
    id: 'mk_webinar', kind: 'traffic_source', layer: 'traffic', code: 'MK_WEBINAR',
    name: 'Вебинар', description: 'Параллельный прогрев. База + рекомендация: рег. на вебинар → после эфира карточка.',
    market: 'BOTH', temperature: 'nurture', formation: ['base', 'recommendation'], lever: ['content', 'time'],
    reactionSpeed: 'weeks', owner: 'crm_lead', medium: 'email', side: 'family',
  },
  {
    id: 'mk_direct', kind: 'traffic_source', layer: 'traffic', code: 'MK_DIRECT',
    name: 'Прямые заходы', description: 'Память / бренд, без UTM. Тёпл–горячий, ведём на главную.',
    market: 'BOTH', temperature: 'warm', temperatureLabel: 'тёпл–гор',
    formation: ['base'], lever: ['time', 'brand'], reactionSpeed: 'months', owner: 'marketing_lead', side: 'family',
  },
];
