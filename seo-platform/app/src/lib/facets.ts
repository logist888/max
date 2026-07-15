// Общие строители data-* атрибутов и конфигов фасетов для фильтр-острова
// (`components/Filters.astro`). Один источник правды для всех страниц-списков:
// /vuzy/, /gorod/, /region/, страницы направления и комбо.
//
// Ключевое правило честности («не выдумывать»): costRange/hasBudget/levels в
// CatalogRow — агрегаты по ВСЕМУ вузу. На странице КОНКРЕТНОГО направления фильтр
// формы/бюджета/цены обязан считаться по офферам именно этого ОКСО —
// `dirOfferFacetData()`, а не из CatalogRow.

import type { CatalogRow, OrgCard, RegionAgg, UgsAgg } from './data.ts';
import type { Facet } from '../components/Filters.astro';

// ---------- data-* строители ----------

/** Полный набор фасетов вуза (агрегаты по всему вузу) — для /vuzy/, /gorod/, /region/.
 *  card нужен для форм обучения и укрупнённых групп (агрегируются из офферов). */
export function orgFacetData(row: CatalogRow, card: OrgCard | undefined): Record<string, string> {
  const forms = new Set<string>();
  const ugsCodes = new Set<string>();
  if (card) {
    for (const o of card.offers) if (o.form) forms.add(o.form);
    for (const g of card.programsByLevel) for (const d of g.directions) if (d.ugs) ugsCodes.add(d.ugs);
  }
  return {
    'data-region': row.regionKey,
    'data-city': row.cityKey,
    'data-kind': row.kind,
    'data-levels': (row.levels ?? []).join(','),
    'data-forms': [...forms].join(','),
    'data-ugs': [...ugsCodes].join(','),
    'data-budget': row.hasBudget ? '1' : '0',
    'data-dorm': row.dormitory ? '1' : '0',
    'data-mil': row.militaryDept ? '1' : '0',
    'data-cost-min': row.costRange ? String(row.costRange.min) : '',
    'data-cost-max': row.costRange ? String(row.costRange.max) : '',
  };
}

/** Честные из CatalogRow атрибуты вуза для страницы НАПРАВЛЕНИЯ/комбо:
 *  география, тип, общежитие, военная кафедра — свойства вуза целиком (честны там).
 *  НЕ включает cost/budget/levels/forms — они по всему вузу и на странице
 *  направления были бы выдумкой; их даёт dirOfferFacetData() по офферам ОКСО. */
export function dirCardFacetData(row: CatalogRow): Record<string, string> {
  return {
    'data-region': row.regionKey,
    'data-city': row.cityKey,
    'data-kind': row.kind,
    'data-dorm': row.dormitory ? '1' : '0',
    'data-mil': row.militaryDept ? '1' : '0',
  };
}

/** Фасеты формы/бюджета/цены ИМЕННО этого направления (okso) в конкретном вузе —
 *  join card→programsByLevel→directions(okso)→offers. Ключи form/budget/cost
 *  отличны от «пофузовских» forms/... , чтобы семантика не смешивалась. */
export function dirOfferFacetData(card: OrgCard | undefined, okso: string): Record<string, string> {
  const forms = new Set<string>();
  let budget = false;
  const costs: number[] = [];
  if (card) {
    for (const g of card.programsByLevel) {
      for (const d of g.directions) {
        if (d.okso !== okso) continue;
        for (const o of d.offers) {
          if (o.form) forms.add(o.form);
          if (o.placeType !== 'Платные места') budget = true;
          if (o.cost !== null) costs.push(o.cost);
        }
      }
    }
  }
  return {
    'data-form': [...forms].join(','),
    'data-budget': budget ? '1' : '0',
    'data-cost-min': costs.length ? String(Math.min(...costs)) : '',
    'data-cost-max': costs.length ? String(Math.max(...costs)) : '',
  };
}

// ---------- готовые конфиги Facet ----------

export const LEVEL_CHIPS = [
  { value: 'Бакалавриат', label: 'Бакалавриат' }, { value: 'Специалитет', label: 'Специалитет' },
  { value: 'Магистратура', label: 'Магистратура' }, { value: 'Аспирантура', label: 'Аспирантура' },
];
export const FORM_CHIPS = [
  { value: 'Очная', label: 'Очная' }, { value: 'Очно-заочная', label: 'Очно-заочная' },
  { value: 'Заочная', label: 'Заочная' },
];
export const KIND_CHIPS = [
  { value: 'головной', label: 'Головной вуз' }, { value: 'филиал', label: 'Филиал' },
  { value: 'зарубежный', label: 'Зарубежный' },
];

export const FACET_KIND: Facet = { key: 'kind', label: 'Тип', type: 'chip', chips: KIND_CHIPS };
export const FACET_LEVELS: Facet = { key: 'levels', label: 'Уровень', type: 'chip', chips: LEVEL_CHIPS };
export const FACET_FORMS: Facet = { key: 'forms', label: 'Форма обучения', type: 'chip', chips: FORM_CHIPS };
export const FACET_FORM: Facet = { key: 'form', label: 'Форма обучения', type: 'chip', chips: FORM_CHIPS };
export const FACET_BUDGET: Facet = { key: 'budget', label: 'Бюджетные места', type: 'toggle', toggleLabel: 'Есть бюджетные места' };
export const FACET_DORM: Facet = { key: 'dorm', label: 'Общежитие', type: 'toggle', toggleLabel: 'Есть общежитие' };
export const FACET_MIL: Facet = { key: 'mil', label: 'Военная подготовка', type: 'toggle', toggleLabel: 'Военная кафедра / УВЦ' };
export const FACET_COST: Facet = { key: 'cost', label: 'Стоимость платного', type: 'range', unit: '₽/год', min: 0, step: 10000 };

/** Регион как select (для длинных списков вузов, где регион варьируется). */
export function regionFacet(regions: RegionAgg[]): Facet {
  return {
    key: 'region', label: 'Регион', type: 'select', placeholder: '— любой регион —',
    options: [...regions].sort((a, b) => a.displayName.localeCompare(b.displayName, 'ru'))
      .map((r) => ({ value: r.key, label: r.displayName })),
  };
}

/** Укрупнённая группа (УГСН) как select. */
export function ugsFacet(ugs: UgsAgg[]): Facet {
  return {
    key: 'ugs', label: 'Направление (укрупнённая группа)', type: 'select', placeholder: '— любая группа —',
    options: [...ugs].sort((a, b) => a.code.localeCompare(b.code))
      .map((g) => ({ value: g.code, label: `${g.code} — ${g.name ?? ''}` })),
  };
}

/** Город как chip-мультивыбор — только для КОРОТКИХ списков (города региона).
 *  Не select: нативный пикер iOS игнорирует option.hidden. value = cityKey. */
export function cityChipFacet(cities: { key: string; name: string }[]): Facet {
  return {
    key: 'city', label: 'Город', type: 'chip',
    chips: [...cities].sort((a, b) => a.name.localeCompare(b.name, 'ru'))
      .map((c) => ({ value: c.key, label: c.name })),
  };
}
