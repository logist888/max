// Нормализация снимка в модель: города, виды организаций, санитария цен,
// акронимы, невыгружаемые уровни. Все правила — из этапов 0–4 проектирования.

import type {
  City, Direction, Model, Offer, Org, OrgKind, RawOrg, Region, SanitationEntry,
} from './types.ts';
import { directionSlug, orgSlug, slugify } from './slugs.ts';

const CITY_PREFIX = /^(г\.|город|пос\.|п\.|с\.|пгт\.?|рп\.?|ст-ца|дер\.|д\.)\s*/i;
const PRICE_SANITY_MIN = 20_000; // ₽/год; ниже — мусор источника (этап 4)

// Организационно-правовой мусор, не являющийся именем вуза.
const ACRO_STOP = new Set([
  'ВО', 'ВПО', 'ДПО', 'ФГБОУ', 'ФГАОУ', 'ФГКОУ', 'ФГБУ', 'ФГАУ', 'ФГБНУ',
  'ГБОУ', 'ГАОУ', 'ГБУ', 'ГАУ', 'ГБУЗ', 'ГАУЗ', 'ФБУН', 'ФКУ', 'АНО',
  'АНОО', 'АНОВО', 'НОУ', 'ЧОУ', 'ЧУ', 'ОУ', 'УВО', 'ОО', 'РФ', 'ИМ',
  'МВД', 'МЧС', 'ФСБ', 'ФСИН', 'МИД', 'МИНЗДРАВА', 'МИНОБРНАУКИ',
]);

function normCityName(raw: string): string {
  return raw.replace(CITY_PREFIX, '').replace(/\s+/g, ' ').trim();
}

// Города федерального значения сами определяют свой субъект: запись
// «Москва / Московская область» — противоречие источника, не факт.
const FEDERAL_CITY_REGION: Record<string, string> = {
  'москва': 'г. Москва',
  'санкт-петербург': 'г. Санкт-Петербург',
  'севастополь': 'г. Севастополь',
};

export interface GeoFix {
  orgId: string;
  region: string;
  evidence: string;
}

function fixedRegion(
  o: RawOrg,
  fixes: Map<string, GeoFix>,
  sanitation: SanitationEntry[],
): string {
  const source = o.region.trim();
  if (source.includes('иностранного')) return source;
  const fix = fixes.get(o.id);
  if (fix && fix.region !== source) {
    sanitation.push({
      orgId: o.id, field: 'region', raw: source,
      reason: `кураторская поправка → «${fix.region}» (${fix.evidence})`,
    });
    return fix.region;
  }
  const federal = FEDERAL_CITY_REGION[normCityName(o.city).toLowerCase()];
  if (federal && federal !== source) {
    sanitation.push({
      orgId: o.id, field: 'region', raw: source,
      reason: `город федерального значения → «${federal}»`,
    });
    return federal;
  }
  return source;
}

function extractAcronyms(shortName: string): string[] {
  const tokens = shortName.match(/[А-ЯЁ]{2,}/g) ?? [];
  return [...new Set(tokens.filter((t) => !ACRO_STOP.has(t)))];
}

function orgKind(o: RawOrg): OrgKind {
  if ((o.region ?? '').includes('иностранного')) return 'зарубежный';
  if (o.name.toLowerCase().includes('филиал')) return 'филиал';
  return 'головной';
}

function toOffers(o: RawOrg, sanitation: SanitationEntry[]): Offer[] {
  return (o.programs ?? []).map((p) => {
    let cost: number | null = null;
    if (p.placeType === 'Платные места') {
      if (p.cost >= PRICE_SANITY_MIN) {
        cost = p.cost;
      } else if (p.cost > 0) {
        sanitation.push({
          orgId: o.id, okso: p.okso, field: 'cost', raw: p.cost,
          reason: `ниже санитарного порога ${PRICE_SANITY_MIN}`,
        });
      }
      // p.cost === 0 на платных — пропуск источника (Д6): остаётся null
    }
    return {
      okso: p.okso, level: p.level, form: p.form, placeType: p.placeType,
      places: p.places > 0 ? p.places : null,
      cost,
    };
  });
}

export function buildModel(
  raw: RawOrg[],
  snapshotDate: string,
  campaignYear: string,
  geoFixes: GeoFix[] = [],
): Model {
  const sanitation: SanitationEntry[] = [];
  const fixIndex = new Map(geoFixes.map((f) => [f.orgId, f]));
  // Эффективный регион каждой организации — после поправок.
  const regionOf = new Map<string, string>(
    raw.map((o) => [o.id, fixedRegion(o, fixIndex, sanitation)]),
  );

  // Регионы
  const regionKeys = new Map<string, Region>();
  for (const o of raw) {
    const name = regionOf.get(o.id)!;
    if (name.includes('иностранного')) continue;
    if (!regionKeys.has(name)) {
      regionKeys.set(name, { key: name, slug: slugify(name), displayName: name });
    }
  }

  // Города: сущность = регион + нормализованное имя (одноимённые города
  // разных регионов не склеиваются). Каноническое написание — самый частый
  // сырой вариант без префикса.
  const cityRaw = new Map<string, { regionKey: string; variants: Map<string, number> }>();
  for (const o of raw) {
    const region = regionOf.get(o.id)!;
    if (region.includes('иностранного')) continue;
    const norm = normCityName(o.city);
    const key = `${region}::${norm.toLowerCase()}`;
    const entry = cityRaw.get(key) ?? { regionKey: region, variants: new Map() };
    entry.variants.set(norm, (entry.variants.get(norm) ?? 0) + 1);
    cityRaw.set(key, entry);
  }
  const cities: City[] = [];
  const slugCount = new Map<string, number>();
  for (const [key, { regionKey, variants }] of cityRaw) {
    const displayName = [...variants.entries()].sort((a, b) => b[1] - a[1])[0]![0];
    cities.push({ key, slug: slugify(displayName), displayName, regionKey, rawNames: [...variants.keys()] });
    slugCount.set(slugify(displayName), (slugCount.get(slugify(displayName)) ?? 0) + 1);
  }
  // Коллизии слагов одноимённых городов: добавляется слаг региона.
  for (const c of cities) {
    if ((slugCount.get(c.slug) ?? 0) > 1) {
      c.slug = `${c.slug}-${slugify(c.regionKey)}`.slice(0, 80);
    }
  }

  // Направления и УГСН
  const directions = new Map<string, Direction>();
  const ugsCodes = new Set<string>();
  for (const o of raw) {
    for (const p of o.programs ?? []) {
      const m = /^\d+\.(\d{2})\.\d{2}\.\d{2}$/.exec(p.okso) ?? /^\d+\.(\d{1,2})/.exec(p.okso);
      const ugs = m?.[1]?.padStart(2, '0') ?? '00';
      ugsCodes.add(ugs);
      if (!directions.has(p.okso)) {
        directions.set(p.okso, {
          okso: p.okso,
          slug: directionSlug(p.okso, p.name),
          name: p.name,
          level: p.level,
          ugsCode: ugs,
        });
      }
    }
  }

  // Организации
  const orgs: Org[] = [];
  const foreignOrgs: Org[] = [];
  for (const o of raw) {
    const kind = orgKind(o);
    const declared = (o.indicators?.['Уровни образования'] ?? '')
      .split('/')
      .map((s) => s.trim())
      .filter(Boolean);
    const offers = toOffers(o, sanitation);
    const exportedLevels = new Set(offers.map((x) => x.level));
    const dormRaw = o.indicators?.['Мест в общежитии'];
    const dormPlaces = dormRaw && /^\d+$/.test(dormRaw) ? Number(dormRaw) : null;
    const norm = normCityName(o.city);
    const region = regionOf.get(o.id)!;

    const org: Org = {
      id: o.id,
      slug: orgSlug(o.shortName, o.id),
      kind,
      shortName: o.shortName.trim(),
      name: o.name.trim(),
      fullName: o.fullName.trim(),
      regionKey: region,
      cityKey: `${region}::${norm.toLowerCase()}`,
      address: o.address?.trim() || null,
      phones: o.phones ?? [],
      emails: o.emails ?? [],
      websites: o.websites ?? [],
      militaryDept: o.militaryDept,
      dormitory: o.dormitory,
      dormPlaces,
      usefulLinks: o.usefulLinks ?? {},
      vk: o.socials?.['vk'] ?? null,
      acronyms: extractAcronyms(o.shortName),
      offers,
      levelsDeclared: declared,
      levelsNotExported: declared.filter((l) => !exportedLevels.has(l)),
    };
    (kind === 'зарубежный' ? foreignOrgs : orgs).push(org);
  }

  return {
    snapshotDate,
    campaignYear,
    orgs,
    foreignOrgs,
    cities,
    regions: [...regionKeys.values()],
    directions: [...directions.values()],
    ugsCodes: [...ugsCodes].sort(),
    sanitation,
  };
}
