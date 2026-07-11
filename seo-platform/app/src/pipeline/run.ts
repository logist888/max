// Конвейер: снимок (.json/.json.gz) → контракт → модель → витрины → build/.
// Идемпотентен: одинаковый вход даёт одинаковый выход.
// Запуск: npm run pipeline -- ../data/universities_2026-07-10.json.gz

import { gunzipSync } from 'node:zlib';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkContract } from './contract.ts';
import { buildModel } from './normalize.ts';
import { buildVitrines } from './vitrines.ts';

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = resolve(HERE, '../..');
const BUILD = join(APP, 'build');

const snapshotArg = process.argv[2] ?? '../data/universities_2026-07-10.json.gz';
const snapshotPath = resolve(APP, snapshotArg);
const SNAPSHOT_DATE = /(\d{4}-\d{2}-\d{2})/.exec(snapshotPath)?.[1] ?? 'unknown';
const CAMPAIGN = '2026/27'; // подтверждено владельцем 11.07.2026

function loadSnapshot(path: string): unknown {
  const buf = readFileSync(path);
  const text = path.endsWith('.gz') ? gunzipSync(buf).toString('utf8') : buf.toString('utf8');
  return JSON.parse(text.replace(/^﻿/, ''));
}

const raw = loadSnapshot(snapshotPath);
const contract = checkContract(raw);
console.log(`Контракт: организаций ${contract.stats.orgs}, записей программ ${contract.stats.offers}, без программ ${contract.stats.orgsWithoutPrograms}`);
for (const w of contract.warnings) console.warn(`  предупреждение: ${w}`);
if (!contract.ok) {
  for (const e of contract.errors) console.error(`  ошибка: ${e}`);
  console.error('Снимок отклонён контрактом.');
  process.exit(1);
}

const geoFixes = (JSON.parse(readFileSync(join(APP, 'config/geo-fixes.json'), 'utf8')) as {
  fixes: { orgId: string; region: string; evidence: string }[];
}).fixes;
const model = buildModel(raw as never, SNAPSHOT_DATE, CAMPAIGN, geoFixes);
const v = buildVitrines(model);

// Проверка целей (поле ручного ввода владельца)
const goals = JSON.parse(readFileSync(join(APP, 'config/goals.json'), 'utf8')) as {
  goals: { code: string; url: string; active: boolean }[];
};
for (const g of goals.goals) {
  if (g.active && !g.url) console.warn(`  предупреждение: цель «${g.code}» активна, но url пуст`);
  if (!g.active) console.log(`  цель «${g.code}»: неактивна (url ${g.url ? 'задан' : 'не задан'})`);
}

mkdirSync(BUILD, { recursive: true });
const write = (name: string, data: unknown) =>
  writeFileSync(join(BUILD, name), JSON.stringify(data));
write('org-cards.json', v.orgCards);
write('catalog-rows.json', v.catalogRows);
write('cities.json', v.cityAgg);
write('regions.json', v.regionAgg);
write('directions.json', v.directionAgg);
write('ugs.json', v.ugsAgg);
write('combos-city.json', v.comboCity);
write('combos-region.json', v.comboRegion);
write('search-export.json', v.searchExport);
write('meta.json', {
  snapshotDate: model.snapshotDate,
  campaignYear: model.campaignYear,
  builtFrom: snapshotArg,
});
write('sanitation-log.json', model.sanitation);

// Отчёт (сверяется с независимыми контролёрами audit_json.py / inventory.py)
const indexableComboCity = v.comboCity.filter((c) => c.indexable).length;
const indexableComboRegion = v.comboRegion.filter((c) => c.indexable).length;
const canonRegion = v.comboRegion.filter((c) => c.canonicalCityKey !== null).length;
const report = {
  orgsRF: model.orgs.length,
  foreign: model.foreignOrgs.length,
  regions: model.regions.length,
  cities: model.cities.length,
  directions: model.directions.length,
  ugs: model.ugsCodes.length,
  comboCityIndexable: indexableComboCity,
  comboRegionIndexable: indexableComboRegion,
  comboRegionCanonicalToCity: canonRegion,
  sanitationEntries: model.sanitation.length,
  orgsWithNotExportedLevels: model.orgs.filter((o) => o.levelsNotExported.length > 0).length,
  canonicalInventory:
    model.orgs.length + model.regions.length + model.cities.length +
    model.directions.length + model.ugsCodes.length +
    indexableComboCity + indexableComboRegion,
};
write('report.json', report);

// Компактный индекс для клиентского острова поиска (локальная фаза R3;
// при выходе на хостинг заменяется Meilisearch — модель документа та же).
// Алиасы длиннее 80 знаков (полные юридические имена) не попадают в индекс:
// их никто не печатает в строку поиска.
const compact = v.searchExport.map((d) => ({
  t: d.type, n: d.title, s: d.subtitle, u: d.url, p: d.popularity,
  a: [...new Set(d.aliases)]
    .filter((al) => al && al.length <= 80 && al !== d.title)
    .map((al) => al.toLowerCase().replace(/ё/g, 'е')),
}));
mkdirSync(join(APP, 'public'), { recursive: true });
writeFileSync(join(APP, 'public/search-index.json'), JSON.stringify(compact));
console.log(`Поисковый индекс: ${compact.length} документов, ` +
  `${Math.round(JSON.stringify(compact).length / 1024)} КБ`);
console.log('Отчёт:', JSON.stringify(report, null, 2));
console.log(`Витрины собраны в ${BUILD}`);
