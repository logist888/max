/**
 * Плоский список свойств сущности для инспектора. Ссылки на другие сущности (канал,
 * посадочная, метрика) разрешаются в человекочитаемые коды. Полностью data-driven.
 */

import type { ID, Inspectable } from '@/types';
import { ENTITY_BY_ID } from '@/data';
import {
  FORMATION_LABEL,
  LANGUAGE_LABEL,
  LEVER_LABEL,
  MARKET_LABEL,
  OWNER_LABEL,
  REACTION_SPEED_LABEL,
  SIDE_LABEL,
  STATUS_LABEL,
  TEMPERATURE_LABEL,
  UTM_MEDIUM_LABEL,
} from '@/data/labels';

export interface Prop {
  readonly k: string;
  readonly v: string;
}

function ref(id: ID): string {
  return ENTITY_BY_ID.get(id)?.code ?? id;
}

export function entityProperties(e: Inspectable): Prop[] {
  switch (e.kind) {
    case 'traffic_source':
      return [
        { k: 'Рынок', v: MARKET_LABEL[e.market] },
        { k: 'Температура', v: e.temperatureLabel ?? TEMPERATURE_LABEL[e.temperature] },
        { k: 'Формирование', v: e.formation.map((f) => FORMATION_LABEL[f]).join(', ') },
        { k: 'Рычаг', v: e.lever.map((l) => LEVER_LABEL[l]).join(' + ') },
        { k: 'Скорость отклика', v: REACTION_SPEED_LABEL[e.reactionSpeed] },
        { k: 'Владелец', v: OWNER_LABEL[e.owner] },
        { k: 'utm_medium', v: e.medium ? UTM_MEDIUM_LABEL[e.medium] : '— (без UTM)' },
        { k: 'Сторона', v: SIDE_LABEL[e.side] },
      ];
    case 'landing':
      return [
        { k: 'Тип', v: e.landingKind === 'funnel' ? 'воронковая' : 'транзакционная' },
        { k: 'Целевое действие', v: e.conversionGoal },
        { k: 'Событие', v: ref(e.targetEventId) },
        { k: 'Следующий шаг', v: e.nextStep },
        ...(e.warmOnly ? [{ k: 'Ограничение', v: 'только тёплый/горячий трафик' }] : []),
      ];
    case 'flow_step':
      return [
        { k: 'Тип шага', v: e.stepKind },
        ...(e.eventCode ? [{ k: 'Код', v: e.eventCode }] : []),
        { k: 'Где хранится', v: e.storedIn },
        { k: 'Источник данных', v: e.dataSource },
        { k: 'Владелец', v: OWNER_LABEL[e.owner] },
        { k: 'Порядок', v: String(e.order) },
      ];
    case 'analytics_node':
      return [
        { k: 'Тип узла', v: e.nodeKind },
        { k: 'Что хранит', v: e.holds },
        ...(e.gap ? [{ k: 'Пробел контура', v: e.gap }] : []),
      ];
    case 'metric':
      return [
        { k: 'Источник данных', v: e.dataSource },
        { k: 'Зелёный', v: e.thresholds.green },
        { k: 'Жёлтый', v: e.thresholds.yellow },
        { k: 'Красный', v: e.thresholds.red },
        { k: 'Проверяет', v: e.checks },
        ...(e.unit ? [{ k: 'Единица', v: e.unit }] : []),
      ];
    case 'decision':
      return [
        { k: 'Метрика', v: ref(e.metricId) },
        { k: 'Условие', v: e.condition },
        { k: 'Действие', v: e.actionLabel },
        ...(e.hypothesis ? [{ k: 'Пометка', v: '[ГИПОТЕЗА] — ставка на скрининг' }] : []),
      ];
    case 'cell':
      return [
        { k: 'Рынок', v: MARKET_LABEL[e.market] },
        { k: 'Язык', v: LANGUAGE_LABEL[e.language] },
        { k: 'Канал', v: ref(e.channelId) },
        { k: 'Посадочная', v: ref(e.landingId) },
        { k: 'Аудитория', v: e.audience },
        { k: 'Креатив', v: e.creative },
        { k: 'Бюджет', v: `$${e.budgetUsd}` },
        { k: 'Владелец', v: OWNER_LABEL[e.owner] },
        { k: 'Статус', v: STATUS_LABEL[e.status] },
        { k: 'utm_campaign', v: e.utmCampaign },
      ];
    case 'rule':
      return [
        { k: 'Температура', v: e.temperatureLabel ?? TEMPERATURE_LABEL[e.temperature] },
        { k: 'Источники', v: e.sourceIds.map(ref).join(', ') },
        { k: 'Осн. посадочная', v: ref(e.primaryLandingId) },
        { k: 'Допустимые', v: e.allowedLandingIds.map(ref).join(', ') || '—' },
        { k: 'Целевое действие', v: e.targetAction },
      ];
    case 'contractor':
      return [
        { k: 'Отчётность', v: e.reporting },
        { k: 'Стоп-правило', v: e.stopRule },
      ];
  }
}
