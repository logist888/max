/**
 * Визуальные соответствия «тип → иконка» (data-слой). Меняется данными, не кодом.
 */

import type { ActionKind, LandingKind, LayerId } from '@/types';
import type { IconKey } from './icons';

export const LANDING_KIND_ICON: Record<LandingKind, IconKey> = {
  funnel: 'file',
  transactional: 'cart',
};

export const ACTION_ICON: Record<ActionKind, IconKey> = {
  fix_creative: 'edit',
  fix_landing: 'wrench',
  scale: 'trendingUp',
  stop: 'octagon',
  pause: 'pause',
  review_product: 'alert',
  monitor: 'gauge',
};

export const LAYER_ICON: Record<LayerId, IconKey> = {
  traffic: 'megaphone',
  landings: 'file',
  platform: 'cursor',
  analytics: 'barChart',
  decisions: 'gauge',
  cell: 'cell',
  contractor: 'clipboard',
};
