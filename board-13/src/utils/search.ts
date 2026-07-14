/**
 * Поиск по всем сущностям: коды, названия, типы, каналы, рынки, CELL, Landing, Event, Decision, Rule.
 * Индекс собирается один раз из ALL_INSPECTABLES; запрос токенизируется и ищется по «сену».
 */

import type { Inspectable } from '@/types';
import { ALL_INSPECTABLES } from '@/data';
import {
  KIND_LABEL,
  MARKET_LABEL,
  LANGUAGE_LABEL,
  STATUS_LABEL,
  TEMPERATURE_LABEL,
  OWNER_LABEL,
} from '@/data/labels';

interface IndexedEntry {
  readonly entity: Inspectable;
  readonly haystack: string;
}

function haystackFor(e: Inspectable): string {
  const parts: string[] = [e.code, e.name, e.description ?? '', KIND_LABEL[e.kind]];
  switch (e.kind) {
    case 'traffic_source':
      parts.push(MARKET_LABEL[e.market], TEMPERATURE_LABEL[e.temperature], OWNER_LABEL[e.owner], e.side);
      break;
    case 'landing':
      parts.push(e.landingKind, e.conversionGoal, e.targetEventId);
      break;
    case 'flow_step':
      parts.push(e.eventCode ?? '', e.storedIn, e.dataSource);
      break;
    case 'analytics_node':
      parts.push(e.holds, e.gap ?? '');
      break;
    case 'metric':
      parts.push(e.checks, e.dataSource);
      break;
    case 'decision':
      parts.push(e.condition, e.actionLabel);
      break;
    case 'cell':
      parts.push(
        MARKET_LABEL[e.market],
        LANGUAGE_LABEL[e.language],
        STATUS_LABEL[e.status],
        OWNER_LABEL[e.owner],
        e.audience,
        e.channelId,
        e.landingId,
      );
      break;
    case 'rule':
      parts.push(e.targetAction, ...e.sourceIds, e.primaryLandingId);
      break;
    case 'contractor':
      parts.push(e.reporting, e.stopRule);
      break;
  }
  return parts.join(' ').toLowerCase();
}

const INDEX: readonly IndexedEntry[] = ALL_INSPECTABLES.map((entity) => ({
  entity,
  haystack: haystackFor(entity),
}));

export interface SearchResult {
  readonly entity: Inspectable;
  readonly score: number;
}

/** Пустой запрос → пустой результат (панель показывает подсказку). */
export function searchEntities(query: string, limit = 24): SearchResult[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const tokens = q.split(/\s+/);
  const results: SearchResult[] = [];
  for (const { entity, haystack } of INDEX) {
    if (!tokens.every((t) => haystack.includes(t))) continue;
    // Оценка: точное совпадение кода/названия — выше.
    const code = entity.code.toLowerCase();
    const name = entity.name.toLowerCase();
    let score = 1;
    if (code === q || name === q) score = 100;
    else if (code.startsWith(q) || name.startsWith(q)) score = 60;
    else if (code.includes(q) || name.includes(q)) score = 30;
    results.push({ entity, score });
  }
  return results.sort((a, b) => b.score - a.score || a.entity.code.localeCompare(b.entity.code)).slice(0, limit);
}
