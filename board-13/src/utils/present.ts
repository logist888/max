/**
 * Отображаемая презентация сущности: иконка, цвет, метки.
 * Единственный мост между доменной моделью и визуальными токенами — узлы/инспектор/поиск
 * не содержат switch по типам сущностей, а спрашивают этот помощник.
 */

import type { Inspectable, UtmMedium } from '@/types';
import type { ColorToken } from '@/data/colors';
import { KIND_COLORS, STATUS_COLORS, TEMPERATURE_COLORS } from '@/data/colors';
import type { IconKey } from '@/data/icons';
import {
  LANDING_KIND_ICON,
  ACTION_ICON,
} from '@/data/visual';
import {
  LANGUAGE_LABEL,
  MARKET_LABEL,
  STATUS_LABEL,
  TEMPERATURE_LABEL,
} from '@/data/labels';

export interface Tag {
  readonly label: string;
  readonly color?: string;
  readonly title?: string;
}

export interface Presentation {
  readonly iconKey: IconKey;
  readonly color: ColorToken;
  readonly tags: readonly Tag[];
}

const MEDIUM_ICON: Record<UtmMedium, IconKey> = {
  cpc: 'target',
  cpm: 'target',
  social: 'share',
  email: 'mail',
  referral: 'link',
  seo: 'search',
  video: 'video',
  pr: 'megaphone',
  affiliate: 'handshake',
  remarketing: 'refresh',
};

export function presentEntity(e: Inspectable): Presentation {
  const color = KIND_COLORS[e.kind];
  switch (e.kind) {
    case 'traffic_source':
      return {
        iconKey: e.medium ? MEDIUM_ICON[e.medium] : 'globe',
        color,
        tags: [
          { label: e.temperatureLabel ?? TEMPERATURE_LABEL[e.temperature], color: TEMPERATURE_COLORS[e.temperature], title: 'Температура' },
          { label: MARKET_LABEL[e.market], title: 'Рынок' },
        ],
      };
    case 'landing':
      return {
        iconKey: LANDING_KIND_ICON[e.landingKind],
        color,
        tags: [
          { label: e.landingKind === 'funnel' ? 'воронковая' : 'транзакционная', title: 'Тип' },
          ...(e.warmOnly ? [{ label: 'тёплый+', color: TEMPERATURE_COLORS.warm, title: 'Только тёплый/горячий' }] : []),
        ],
      };
    case 'flow_step':
      return { iconKey: e.iconKey, color, tags: e.eventCode ? [{ label: e.eventCode }] : [] };
    case 'analytics_node':
      return {
        iconKey: e.iconKey,
        color,
        tags: e.gap ? [{ label: 'пробел контура', color: '#ef4444', title: e.gap }] : [],
      };
    case 'metric':
      return { iconKey: 'gauge', color, tags: e.unit ? [{ label: e.unit }] : [] };
    case 'decision':
      return { iconKey: ACTION_ICON[e.action], color, tags: [{ label: e.actionLabel }] };
    case 'cell':
      return {
        iconKey: 'cell',
        color,
        tags: [
          { label: STATUS_LABEL[e.status], color: STATUS_COLORS[e.status], title: 'Статус' },
          { label: MARKET_LABEL[e.market], title: 'Рынок' },
          { label: LANGUAGE_LABEL[e.language], title: 'Язык' },
        ],
      };
    case 'contractor':
      return { iconKey: 'clipboard', color, tags: [{ label: 'шаблон запуска' }] };
    case 'rule':
      return { iconKey: 'sliders', color, tags: [{ label: e.targetAction }] };
  }
}
