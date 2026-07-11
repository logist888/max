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

export interface DirectionAgg {
  okso: string; slug: string; name: string; level: string; ugsCode: string;
  orgCount: number; cityCount: number; costRange: CostRange | null; hasBudget: boolean;
}

export interface UgsAgg { code: string; directions: string[] }

export interface ComboCity {
  okso: string; cityKey: string; orgIds: string[]; indexable: boolean;
}

export interface ComboRegion {
  okso: string; regionKey: string; orgIds: string[];
  indexable: boolean; canonicalCityKey: string | null;
}

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
  directions: DirectionAgg[]; ugs: UgsAgg[];
  combosCity: ComboCity[]; combosRegion: ComboRegion[];
  rowById: Map<string, CatalogRow>;
  cardById: Map<string, OrgCard>;
  cityByKey: Map<string, CityAgg>;
  directionByOkso: Map<string, DirectionAgg>;
  regionByKey: Map<string, RegionAgg>;
  /** ОКСО → строки каталога вузов, где направление есть */
  rowsByOkso: Map<string, CatalogRow[]>;
} | null = null;

export function db() {
  if (cache) return cache;
  const orgCards = load<OrgCard[]>('org-cards.json');
  const catalogRows = load<CatalogRow[]>('catalog-rows.json');
  const cities = load<CityAgg[]>('cities.json');
  const regions = load<RegionAgg[]>('regions.json');
  const meta = load<Meta>('meta.json');
  const directions = load<DirectionAgg[]>('directions.json');
  const ugs = load<UgsAgg[]>('ugs.json');
  const combosCity = load<ComboCity[]>('combos-city.json');
  const combosRegion = load<ComboRegion[]>('combos-region.json');
  assertUniqueSlugs(orgCards, 'вуз');
  assertUniqueSlugs(cities, 'город');
  assertUniqueSlugs(regions, 'регион');
  assertUniqueSlugs(directions, 'направление');
  // Каталог отсортирован стабильно: по числу направлений, затем по имени.
  catalogRows.sort((a, b) =>
    b.directionsCount - a.directionsCount || a.shortName.localeCompare(b.shortName, 'ru'));

  const rowById = new Map(catalogRows.map((r) => [r.id, r]));
  const cardById = new Map(orgCards.map((c) => [c.id, c]));
  const cityByKey = new Map(cities.map((c) => [c.key, c]));
  const directionByOkso = new Map(directions.map((d) => [d.okso, d]));
  const regionByKey = new Map(regions.map((r) => [r.key, r]));
  const rowsByOkso = new Map<string, CatalogRow[]>();
  for (const card of orgCards) {
    const row = rowById.get(card.id)!;
    const seen = new Set<string>();
    for (const group of card.programsByLevel) {
      for (const dir of group.directions) {
        if (seen.has(dir.okso)) continue;
        seen.add(dir.okso);
        const arr = rowsByOkso.get(dir.okso);
        if (arr) arr.push(row);
        else rowsByOkso.set(dir.okso, [row]);
      }
    }
  }
  cache = {
    orgCards, catalogRows, cities, regions, meta, directions, ugs,
    combosCity, combosRegion, rowById, cardById, cityByKey, directionByOkso, regionByKey, rowsByOkso,
  };
  return cache;
}
