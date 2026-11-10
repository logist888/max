// Витрины чтения (этап 1): плоские структуры, из которых сайт рендерит
// страницы без соединений. Пороги индексации комбинаций — этап 2.

import type { Model, Offer, Org } from './types.ts';

const COMBO_CITY_MIN_ORGS = 2; // «направление × город»
const COMBO_REGION_MIN_ORGS = 2; // «направление × регион»
const COMBO_REGION_MIN_CITIES = 2; // иначе canonical на городскую

export interface CostRange {
  min: number;
  max: number;
}

function costRange(offers: Offer[]): CostRange | null {
  const costs = offers.filter((o) => o.cost !== null).map((o) => o.cost!) ;
  if (costs.length === 0) return null;
  return { min: Math.min(...costs), max: Math.max(...costs) };
}

function hasBudget(offers: Offer[]): boolean {
  return offers.some((o) => o.placeType !== 'Платные места');
}

export function buildVitrines(model: Model, ugsNames: Record<string, string> = {}) {
  const cityByKey = new Map(model.cities.map((c) => [c.key, c]));
  const regionByKey = new Map(model.regions.map((r) => [r.key, r]));
  const dirByOkso = new Map(model.directions.map((d) => [d.okso, d]));

  // ---- Карточки вузов и строки каталога
  const orgCards = model.orgs.map((org) => {
    const city = cityByKey.get(org.cityKey)!;
    const byLevel = new Map<string, Map<string, Offer[]>>(); // уровень → ОКСО → позиции
    for (const off of org.offers) {
      const lvl = byLevel.get(off.level) ?? new Map<string, Offer[]>();
      const arr = lvl.get(off.okso) ?? [];
      arr.push(off);
      lvl.set(off.okso, arr);
      byLevel.set(off.level, lvl);
    }
    const directionsCount = new Set(org.offers.map((o) => o.okso)).size;
    return {
      ...org,
      citySlug: city.slug,
      cityName: city.displayName,
      regionSlug: regionByKey.get(org.regionKey)!.slug,
      directionsCount, // счёт из списка программ; счётчик источника не публикуется (Д4)
      costRange: costRange(org.offers),
      hasBudget: hasBudget(org.offers),
      programsByLevel: [...byLevel.entries()].map(([level, dirs]) => ({
        level,
        directions: [...dirs.entries()].map(([okso, offers]) => ({
          okso,
          slug: dirByOkso.get(okso)!.slug,
          name: dirByOkso.get(okso)!.name,
          ugs: dirByOkso.get(okso)!.ugsCode,
          offers,
        })),
      })),
    };
  });

  const catalogRows = orgCards.map((c) => ({
    id: c.id, slug: c.slug, kind: c.kind, shortName: c.shortName,
    cityKey: c.cityKey, citySlug: c.citySlug, cityName: c.cityName,
    regionKey: c.regionKey, regionSlug: c.regionSlug,
    directionsCount: c.directionsCount, costRange: c.costRange,
    hasBudget: c.hasBudget, militaryDept: c.militaryDept, dormitory: c.dormitory,
    levels: [...new Set(c.offers.map((o) => o.level))],
  }));

  // ---- Агрегаты географии
  const orgsByCity = groupBy(model.orgs, (o) => o.cityKey);
  const cityAgg = model.cities.map((c) => {
    const orgs = orgsByCity.get(c.key) ?? [];
    const offers = orgs.flatMap((o) => o.offers);
    return {
      ...c,
      orgCount: orgs.length,
      directionCount: new Set(offers.map((o) => o.okso)).size,
      costRange: costRange(offers),
      orgSlugs: orgs.map((o) => o.slug),
    };
  });
  const orgsByRegion = groupBy(model.orgs, (o) => o.regionKey);
  const regionAgg = model.regions.map((r) => {
    const orgs = orgsByRegion.get(r.key) ?? [];
    const cities = model.cities.filter((c) => c.regionKey === r.key);
    return {
      ...r,
      orgCount: orgs.length,
      cities: cities.map((c) => ({ slug: c.slug, name: c.displayName,
        orgCount: (orgsByCity.get(c.key) ?? []).length })),
    };
  });

  // ---- Агрегаты направлений и УГСН
  const offerIndex: { org: Org; offer: Offer }[] = model.orgs.flatMap((org) =>
    org.offers.map((offer) => ({ org, offer })));
  const byOkso = groupBy(offerIndex, (x) => x.offer.okso);
  const directionAgg = model.directions.map((d) => {
    const entries = byOkso.get(d.okso) ?? [];
    const orgIds = new Set(entries.map((e) => e.org.id));
    return {
      ...d,
      orgCount: orgIds.size,
      cityCount: new Set(entries.map((e) => e.org.cityKey)).size,
      costRange: costRange(entries.map((e) => e.offer)),
      hasBudget: entries.some((e) => e.offer.placeType !== 'Платные места'),
    };
  });
  // Число вузов на каждую УГСН — по всем ФГОС-направлениям группы.
  const orgsByUgs = new Map<string, Set<string>>();
  for (const { org, offer } of offerIndex) {
    const d = dirByOkso.get(offer.okso);
    if (!d || !d.ugsCode) continue;
    const set = orgsByUgs.get(d.ugsCode) ?? new Set<string>();
    set.add(org.id);
    orgsByUgs.set(d.ugsCode, set);
  }
  const ugsAgg = model.ugsCodes.sort().map((code) => {
    const dirs = model.directions.filter((d) => d.ugsCode === code);
    return {
      code,
      // Название — из кураторского справочника config/ugs-names.json
      // (перечень УГСН Минобрнауки). Нет названия — показываем «Группа {код}».
      name: ugsNames[code] ?? null,
      directionCount: dirs.length,
      orgCount: (orgsByUgs.get(code) ?? new Set()).size,
      // до трёх реальных примеров направлений группы (для превью), без дублей
      sample: [...new Set(dirs.map((d) => d.name))]
        .sort((a, b) => a.localeCompare(b, 'ru'))
        .slice(0, 3),
    };
  });

  // Научные специальности (аспирантура/ординатура) — вне УГСН, отдельно.
  const sciByOkso = groupBy(offerIndex.filter((x) => dirByOkso.get(x.offer.okso)?.scientific),
    (x) => x.offer.okso);
  const scientificAgg = model.directions
    .filter((d) => d.scientific)
    .map((d) => ({
      okso: d.okso, slug: d.slug, name: d.name, level: d.level,
      orgCount: new Set((sciByOkso.get(d.okso) ?? []).map((e) => e.org.id)).size,
    }))
    .sort((a, b) => b.orgCount - a.orgCount || a.name.localeCompare(b.name, 'ru'));

  // ---- Комбинации с порогами этапа 2
  const comboCity: {
    okso: string; cityKey: string; orgIds: string[]; indexable: boolean;
  }[] = [];
  const byOksoCity = groupBy(offerIndex, (x) => `${x.offer.okso}::${x.org.cityKey}`);
  for (const [key, entries] of byOksoCity) {
    const [okso, ...rest] = key.split('::');
    const cityKey = rest.join('::');
    const orgIds = [...new Set(entries.map((e) => e.org.id))];
    comboCity.push({ okso: okso!, cityKey, orgIds, indexable: orgIds.length >= COMBO_CITY_MIN_ORGS });
  }
  const comboRegion: {
    okso: string; regionKey: string; orgIds: string[];
    indexable: boolean; canonicalCityKey: string | null;
  }[] = [];
  const byOksoRegion = groupBy(offerIndex, (x) => `${x.offer.okso}::${x.org.regionKey}`);
  for (const [key, entries] of byOksoRegion) {
    const [okso, regionKey] = key.split('::') as [string, string];
    const orgIds = [...new Set(entries.map((e) => e.org.id))];
    const cityKeys = [...new Set(entries.map((e) => e.org.cityKey))];
    const enough = orgIds.length >= COMBO_REGION_MIN_ORGS;
    comboRegion.push({
      okso, regionKey, orgIds,
      indexable: enough && cityKeys.length >= COMBO_REGION_MIN_CITIES,
      canonicalCityKey: enough && cityKeys.length === 1 ? cityKeys[0]! : null,
    });
  }

  // ---- Экспорт для поиска (этап 3: сущность + алиасы)
  const searchExport = [
    ...orgCards.map((c) => ({
      type: 'org', id: c.id, title: c.shortName, subtitle: `${c.cityName}, ${c.regionKey}`,
      aliases: [...new Set([c.shortName, c.name, ...c.acronyms])],
      popularity: c.offers.length, url: `/vuz/${c.slug}/`,
    })),
    ...directionAgg.map((d) => ({
      type: 'direction', id: d.okso, title: d.name, subtitle: `${d.level} · вузов: ${d.orgCount}`,
      aliases: [d.name, d.okso.replace(/^\d+\./, '')],
      popularity: d.orgCount, url: `/specialnost/${d.slug}/`,
    })),
    ...cityAgg.filter((c) => c.orgCount > 0).map((c) => ({
      type: 'city', id: c.key, title: c.displayName, subtitle: c.regionKey,
      aliases: c.rawNames, popularity: c.orgCount, url: `/gorod/${c.slug}/`,
    })),
    ...regionAgg.map((r) => ({
      type: 'region', id: r.key, title: r.displayName, subtitle: `вузов: ${r.orgCount}`,
      aliases: [r.displayName], popularity: r.orgCount, url: `/region/${r.slug}/`,
    })),
  ];

  return {
    orgCards, catalogRows, cityAgg, regionAgg, directionAgg, ugsAgg, scientificAgg,
    comboCity, comboRegion, searchExport,
  };
}

function groupBy<T>(items: T[], key: (item: T) => string): Map<string, T[]> {
  const map = new Map<string, T[]>();
  for (const item of items) {
    const k = key(item);
    const arr = map.get(k);
    if (arr) arr.push(item);
    else map.set(k, [item]);
  }
  return map;
}
