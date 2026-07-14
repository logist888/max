// Средний балл ЕГЭ зачисленных (ВШЭ, Мониторинг качества приёма, 2025) по вузам.
// Источник — data/hse/hse-scores.json (собран scripts/build_hse_scores.py из открытых
// таблиц ege.hse.ru; связка с нашими вузами — фаззи по названию+городу, высококонфидентно).
//
// ВАЖНО: это СРЕДНИЙ балл зачисленных, НЕ проходной. Где вуз не сматчился — записи нет
// (на странице «Информация отсутствует»). Ключ — slug нашего вуза.

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

export interface VuzScore {
  budget: number | null;
  paid: number | null;
  nBudget: number | null;
  year: number;
  hseName: string;
}

let cache: Record<string, VuzScore> | null = null;

export function vuzScores(): Record<string, VuzScore> {
  if (cache) return cache;
  try {
    cache = JSON.parse(readFileSync(resolve(process.cwd(), '../data/hse/hse-scores.json'), 'utf8'));
  } catch {
    cache = {};
  }
  return cache!;
}
