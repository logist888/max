// Доступ сайта к витринам конвейера. Сайт читает только эти структуры —
// мимо витрин в снимок никто не ходит (слои этапа 6).

import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

// Сборка сайта запускается из каталога app/ — путь от рабочего каталога,
// а не от import.meta.url: после бандлинга Astro модуль живёт в dist/.
const BUILD = resolve(process.cwd(), 'build');

export interface CostRange { min: number; max: number }

export interface OfferView {
  okso: string; level: string; form: string; placeType: string;
  places: number | null; cost: number | null;
}

export interface OrgCard {
  id: string; slug: string; kind: 'головной' | 'филиал' | 'зарубежный';
  shortName: string; name: string; fullName: string;
  regionKey: string; regionSlug: string;
  cityKey: string; citySlug: string; cityName: string;
  address: string | null; phones: string[]; emails: string[]; websites: string[];
  militaryDept: boolean; dormitory: boolean; dormPlaces: number | null;
  usefulLinks: Record<string, string>; vk: string | null;
  acronyms: string[]; directionsCount: number;
  costRange: CostRange | null; hasBudget: boolean;
  levelsDeclared: string[]; levelsNotExported: string[];
  offers: OfferView[];
  programsByLevel: {
    level: string;
    directions: { okso: string; slug: string; name: string; ugs: string; offers: OfferView[] }[];
  }[];
}

export interface CatalogRow {
  id: string; slug: string; kind: string; shortName: string;
  cityKey: string; citySlug: string; cityName: string;
  regionKey: string; regionSlug: string;
  directionsCount: number; costRange: CostRange | null;
  hasBudget: boolean; militaryDept: boolean; dormitory: boolean; levels: string[];
}

export interface CityAgg {
  key: string; slug: string; displayName: string; regionKey: string;
  rawNames: string[]; orgCount: number; directionCount: number;
  costRange: CostRange | null; orgSlugs: string[];
}

export interface RegionAgg {
  key: string; slug: string; displayName: string; orgCount: number;
  cities: { slug: string; name: string; orgCount: number }[];
}

export interface Meta { snapshotDate: string; campaignYear: string }

function load<T>(name: string): T {
  return JSON.parse(readFileSync(join(BUILD, name), 'utf8')) as T;
}

function assertUniqueSlugs(items: { slug: string }[], what: string): void {
  const seen = new Set<string>();
  for (const it of items) {
    if (seen.has(it.slug)) throw new Error(`дубль слага (${what}): ${it.slug}`);
    seen.add(it.slug);
  }
}

let cache: {
  orgCards: OrgCard[]; catalogRows: CatalogRow[]; cities: CityAgg[];
  regions: RegionAgg[]; meta: Meta;
} | null = null;

export function db() {
  if (cache) return cache;
  const orgCards = load<OrgCard[]>('org-cards.json');
  const catalogRows = load<CatalogRow[]>('catalog-rows.json');
  const cities = load<CityAgg[]>('cities.json');
  const regions = load<RegionAgg[]>('regions.json');
  const meta = load<Meta>('meta.json');
  assertUniqueSlugs(orgCards, 'вуз');
  assertUniqueSlugs(cities, 'город');
  assertUniqueSlugs(regions, 'регион');
  // Каталог отсортирован стабильно: по числу направлений, затем по имени.
  catalogRows.sort((a, b) =>
    b.directionsCount - a.directionsCount || a.shortName.localeCompare(b.shortName, 'ru'));
  cache = { orgCards, catalogRows, cities, regions, meta };
  return cache;
}
