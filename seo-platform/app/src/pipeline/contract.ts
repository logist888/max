// Входной контракт снимка: снимок, не прошедший проверки, не принимается.
// Дублирует независимый контролёр seo-platform/audit_json.py — расхождение
// их выводов само по себе повод для разбирательства.

import type { RawOrg } from './types.ts';

export const KNOWN_LEVELS = new Set([
  'Бакалавриат',
  'Специалитет',
  'Магистратура',
  'Аспирантура',
  'Базовое высшее образование',
  'Специализированное высшее образование',
]);

export const KNOWN_FORMS = new Set(['Очная', 'Очно-заочная', 'Заочная']);

export const KNOWN_PLACE_TYPES = new Set([
  'Платные места',
  'Основные места в рамках КЦП',
  'Отдельная квота',
  'Особая квота',
  'Целевая детализированная квота',
  'Целевая недетализированная квота',
]);

export interface ContractReport {
  ok: boolean;
  errors: string[];
  warnings: string[];
  stats: {
    orgs: number;
    offers: number;
    orgsWithoutPrograms: number;
  };
}

export function checkContract(data: unknown): ContractReport {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!Array.isArray(data)) {
    return {
      ok: false,
      errors: ['снимок не является массивом организаций'],
      warnings,
      stats: { orgs: 0, offers: 0, orgsWithoutPrograms: 0 },
    };
  }
  const orgs = data as RawOrg[];

  const ids = new Set<string>();
  let offers = 0;
  let noPrograms = 0;

  for (const o of orgs) {
    const label = `org ${o?.id ?? '<без id>'}`;
    for (const field of ['id', 'name', 'fullName', 'shortName', 'region', 'city', 'url'] as const) {
      if (typeof o?.[field] !== 'string' || o[field].trim() === '') {
        errors.push(`${label}: пустое обязательное поле ${field}`);
      }
    }
    if (ids.has(o.id)) errors.push(`${label}: дубль id`);
    ids.add(o.id);
    if (typeof o.militaryDept !== 'boolean' || typeof o.dormitory !== 'boolean') {
      errors.push(`${label}: флаги militaryDept/dormitory не булевы`);
    }

    const progs = o.programs ?? [];
    if (progs.length === 0) noPrograms += 1;
    for (const p of progs) {
      offers += 1;
      if (!p.okso || !p.name) errors.push(`${label}: программа без okso/name`);
      if (!KNOWN_LEVELS.has(p.level)) errors.push(`${label}: неизвестный уровень «${p.level}»`);
      if (!KNOWN_FORMS.has(p.form)) errors.push(`${label}: неизвестная форма «${p.form}»`);
      if (!KNOWN_PLACE_TYPES.has(p.placeType)) {
        errors.push(`${label}: неизвестный тип мест «${p.placeType}»`);
      }
      if (typeof p.places !== 'number' || p.places < 0) {
        errors.push(`${label}: некорректные места ${p.places} (${p.okso})`);
      }
      if (typeof p.cost !== 'number' || p.cost < 0) {
        errors.push(`${label}: некорректная стоимость ${p.cost} (${p.okso})`);
      }
    }
  }

  // Пределы разумности объёма: резкое отклонение — сигнал битого экспорта
  // (урок этапа 0: обрезка на 30 000 символов выглядела «почти нормально»).
  if (orgs.length < 1500 || orgs.length > 2500) {
    warnings.push(`организаций ${orgs.length} — вне ожидаемого коридора 1500–2500`);
  }
  if (offers < 80_000) {
    warnings.push(`записей программ ${offers} — меньше ожидаемых ~100 тыс., проверить полноту экспорта`);
  }

  const cap = 30;
  if (errors.length > cap) {
    errors.splice(cap);
    errors.push('…и другие ошибки (обрезано)');
  }
  return {
    ok: errors.length === 0,
    errors,
    warnings,
    stats: { orgs: orgs.length, offers, orgsWithoutPrograms: noPrograms },
  };
}
