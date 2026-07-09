/**
 * Фильтры: рынок, язык, источник, температура, тип посадочной, статус, владелец.
 * Каждый фасет ограничивает только те узлы, у которых соответствующий атрибут есть;
 * общие узлы (шаги воронки, аналитика) фильтром не приглушаются.
 */

import type {
  CellStatus,
  ID,
  Language,
  LandingKind,
  Market,
  OwnerRole,
  Temperature,
} from '@/types';
import type { GraphNode } from '@/types/graph';

export interface FilterState {
  readonly markets: ReadonlySet<Market>;
  readonly languages: ReadonlySet<Language>;
  readonly channels: ReadonlySet<ID>;
  readonly temperatures: ReadonlySet<Temperature>;
  readonly landingKinds: ReadonlySet<LandingKind>;
  readonly statuses: ReadonlySet<CellStatus>;
  readonly owners: ReadonlySet<OwnerRole>;
}

export const EMPTY_FILTERS: FilterState = {
  markets: new Set(),
  languages: new Set(),
  channels: new Set(),
  temperatures: new Set(),
  landingKinds: new Set(),
  statuses: new Set(),
  owners: new Set(),
};

export function isFiltersActive(f: FilterState): boolean {
  return (
    f.markets.size > 0 ||
    f.languages.size > 0 ||
    f.channels.size > 0 ||
    f.temperatures.size > 0 ||
    f.landingKinds.size > 0 ||
    f.statuses.size > 0 ||
    f.owners.size > 0
  );
}

function marketOk(market: Market, sel: ReadonlySet<Market>): boolean {
  if (sel.size === 0) return true;
  if (market === 'BOTH') return true; // применим к любому выбранному рынку
  return sel.has(market);
}

/** true → узел проходит фильтры (не приглушается). */
export function nodeMatchesFilters(node: GraphNode, f: FilterState): boolean {
  const e = node.entity;
  if (!e) return true;

  switch (e.kind) {
    case 'traffic_source':
      if (!marketOk(e.market, f.markets)) return false;
      if (f.temperatures.size > 0 && !f.temperatures.has(e.temperature)) return false;
      if (f.owners.size > 0 && !f.owners.has(e.owner)) return false;
      if (f.channels.size > 0 && !f.channels.has(e.id)) return false;
      return true;
    case 'landing':
      if (f.landingKinds.size > 0 && !f.landingKinds.has(e.landingKind)) return false;
      return true;
    case 'cell':
      if (!marketOk(e.market, f.markets)) return false;
      if (f.languages.size > 0 && !f.languages.has(e.language)) return false;
      if (f.channels.size > 0 && !f.channels.has(e.channelId)) return false;
      if (f.statuses.size > 0 && !f.statuses.has(e.status)) return false;
      if (f.owners.size > 0 && !f.owners.has(e.owner)) return false;
      return true;
    case 'flow_step':
      if (f.owners.size > 0 && !f.owners.has(e.owner)) return false;
      return true;
    default:
      return true;
  }
}
