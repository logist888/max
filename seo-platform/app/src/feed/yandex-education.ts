// Генератор YML-фида для Яндекса, формат «Образовательные онлайн-курсы и уроки»
// (yandex.ru/support/webmaster/ru/search-appearance/education.html).
//
// ВАЖНО, ПРОЧИТАТЬ ПЕРЕД ОТПРАВКОЙ. Формат рассчитан на площадки, которые сами
// проводят обучение онлайн: «Сайты, предлагающие курсы и другие образовательные
// услуги, которые проводятся онлайн». ВУЗ-навигатор — справочник вузов, обучение
// не проводит и не продаёт. Фид собран по прямому указанию владельца; перед
// загрузкой нужно понимать три вынужденных допущения:
//
//   1. Категория. Рубрикатор Яндекса — каталог тем онлайн-курсов, раздела для
//      высшего образования в нём нет. Ближайшее — «Переподготовка» и «Изучение
//      наук»; соответствие приблизительное (см. UGS_CATEGORY ниже).
//   2. Цена. Яндекс просит «стоимость за весь курс». У нас в данных только
//      стоимость за учебный год, и срок обучения источник не даёт. В price
//      уходит минимальная годовая стоимость, а в description это сказано прямо.
//   3. «Ссылка на контент курса» не передаётся: поле необязательное, а внутренней
//      страницы обучения у справочника нет. Выдумывать её нельзя.
//
// Единица предложения — страница: направление и «направление × город». У каждой
// есть собственный канонический адрес, требование уникальности url выполняется.
// Пары «вуз × направление» единицей быть не могут — отдельной страницы у них нет.

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';

const BUILD = resolve(process.cwd(), 'build');
const OUT = resolve(process.cwd(), 'dist', 'yandex-education.yml');
const SITE = process.env.SITE_URL || 'https://vuz-navigator.ru';
// Адрес для обращений по курсам — обязательное поле фида. Задаётся переменной
// окружения, чтобы не зашивать в код чужой контакт.
const EMAIL = process.env.FEED_EMAIL || 'info@vuz-navigator.ru';
// Лимит Яндекса — 30 000 предложений в одном фиде.
const MAX_OFFERS = 30000;

interface Direction {
  okso: string; slug: string; name: string; level: string; ugsCode: string;
  scientific: boolean; orgCount: number; cityCount: number;
  costRange: { min: number; max: number } | null; hasBudget: boolean;
}
interface ComboCity { okso: string; cityKey: string; orgIds: string[]; indexable: boolean }
interface City { key: string; slug: string; name: string; displayName: string }
interface Offer {
  id: string; name: string; url: string; categoryId: number;
  price: number; description: string;
}

const read = <T>(f: string): T => JSON.parse(readFileSync(resolve(BUILD, f), 'utf8')) as T;

// Соответствие укрупнённых групп (первые две цифры ОКСО) категориям рубрикатора
// Яндекса. Точного соответствия нет: в рубрикаторе нет высшего образования,
// поэтому берётся ближайшая по предметной области категория.
//   900/901–904 — «Изучение наук» (точные, технические, естественные, социальные)
//   1001–1013   — «Переподготовка» по отраслям
//   100         — «Программирование», 600 — «Творчество»
const UGS_CATEGORY: Record<string, number> = {
  '01': 901, '03': 901, '16': 902, '27': 902, '28': 902,
  '02': 100, '09': 100, '10': 100,
  '04': 903, '05': 903, '06': 903,
  '07': 1001, '08': 1001,
  '11': 1007, '12': 1007, '13': 1007, '14': 1007, '17': 1007, '18': 1007,
  '21': 1007, '22': 1007, '29': 1007,
  '15': 1010, '23': 1010, '24': 1010, '25': 1010, '26': 1010,
  '19': 1013, '20': 1013,
  '30': 1006, '31': 1006, '32': 1006, '33': 1006, '34': 1006,
  '35': 1099, '36': 1099, '48': 999, '45': 999,
  '37': 904, '41': 904, '42': 904, '46': 904, '47': 904,
  '38': 1003, '39': 1009, '40': 1004, '43': 1011, '44': 1008, '49': 1012,
  '50': 600, '51': 600, '52': 600, '53': 600, '54': 600, '55': 600,
};
const FALLBACK = 999; // «Изучение наук → Разное»

// Научные специальности (аспирантура) живут в своей номенклатуре, УГСН у них нет.
// Первая цифра кода — отрасль науки: 1 естественные, 2 технические, 3 медицинские,
// 4 сельскохозяйственные, 5 социально-гуманитарные.
const SCI_CATEGORY: Record<string, number> = {
  '1': 903, '2': 902, '3': 1006, '4': 1099, '5': 904,
};

function categoryOf(d: Direction): number {
  if (d.ugsCode) return UGS_CATEGORY[d.ugsCode.slice(0, 2)] ?? FALLBACK;
  const branch = d.okso.split('.')[0];
  return SCI_CATEGORY[branch] ?? FALLBACK;
}

const rub = (n: number) => n.toLocaleString('ru-RU').replace(/ /g, ' ');
const esc = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
   .replace(/"/g, '&quot;').replace(/'/g, '&apos;');
// Код для показа: у ФГОС первая цифра — служебная область образования и срезается,
// у научных специальностей код трёхчастный целиком (3.1.7 «Стоматология»).
const codeOf = (okso: string) => okso.split('.').length === 4 ? okso.replace(/^\d+\./, '') : okso;

function main() {
  const directions = read<Direction[]>('directions.json');
  const combos = read<ComboCity[]>('combos-city.json');
  const citiesRaw = read<City[] | Record<string, City>>('cities.json');
  const cities: City[] = Array.isArray(citiesRaw) ? citiesRaw : Object.values(citiesRaw);
  const cityByKey = new Map(cities.map((c) => [c.key, c]));
  const meta = read<{ campaignYear: string; snapshotDate: string }>('meta.json');
  const dirByOkso = new Map(directions.map((d) => [d.okso, d]));

  const offers: Offer[] = [];
  const seenUrl = new Set<string>();
  const push = (o: Offer) => {
    if (seenUrl.has(o.url)) return;           // url обязан быть уникальным
    seenUrl.add(o.url);
    offers.push(o);
  };

  // 1. Страницы направлений.
  for (const d of directions) {
    if (!d.costRange) continue;               // без цены предложение не собрать
    const url = `${SITE}/specialnost/${d.slug}/`;
    push({
      id: `dir-${d.slug}`,
      name: `${d.name} — ${d.level.toLowerCase()}`,
      url,
      categoryId: categoryOf(d),
      price: d.costRange.min,
      description:
        `Направление подготовки ${codeOf(d.okso)} «${d.name}», ${d.level.toLowerCase()}. ` +
        `${d.orgCount} вузов в ${d.cityCount} городах России. ` +
        `Стоимость платного обучения — от ${rub(d.costRange.min)} до ${rub(d.costRange.max)} ₽ ` +
        `за учебный год (в поле «цена» указана минимальная годовая стоимость; ` +
        `полную стоимость обучения источник не публикует).` +
        (d.hasBudget ? ' Есть бюджетные места.' : '') +
        ` Данные приёмной кампании ${meta.campaignYear} из выгрузки «ВУЗ-навигатора» ` +
        `Госуслуг от ${meta.snapshotDate}. Обучение очное, в вузе; ` +
        `ВУЗ-навигатор — справочник и сам обучение не проводит.`,
    });
  }

  // 2. «Направление × город» — только индексируемые комбинации.
  for (const c of combos) {
    if (!c.indexable) continue;
    const d = dirByOkso.get(c.okso);
    const city = cityByKey.get(c.cityKey);
    if (!d || !city || !d.costRange) continue;
    push({
      id: `combo-${d.slug}-${city.slug}`,
      name: `${d.name} — ${d.level.toLowerCase()}, ${city.name}`,
      url: `${SITE}/specialnost/${d.slug}/${city.slug}/`,
      categoryId: categoryOf(d),
      price: d.costRange.min,
      description:
        `Направление ${codeOf(d.okso)} «${d.name}» (${d.level.toLowerCase()}) в городе ${city.name}: ` +
        `${c.orgIds.length} вузов. Стоимость платного обучения по направлению — ` +
        `от ${rub(d.costRange.min)} ₽ за учебный год (минимальная годовая по России; ` +
        `полную стоимость обучения источник не публикует).` +
        (d.hasBudget ? ' Есть бюджетные места.' : '') +
        ` Данные приёмной кампании ${meta.campaignYear} из выгрузки «ВУЗ-навигатора» ` +
        `Госуслуг от ${meta.snapshotDate}. Обучение очное, в вузе; ` +
        `ВУЗ-навигатор — справочник и сам обучение не проводит.`,
    });
  }

  if (offers.length > MAX_OFFERS) {
    console.error(`Предложений ${offers.length} — больше лимита Яндекса ${MAX_OFFERS}. ` +
      'Фид нужно разбить на части.');
    process.exit(1);
  }

  const now = new Date().toISOString().slice(0, 19);
  const lines: string[] = [];
  lines.push('<?xml version="1.0" encoding="UTF-8"?>');
  lines.push(`<yml_catalog date="${now}">`);
  lines.push('  <shop>');
  lines.push('    <name>ВУЗ-навигатор</name>');
  lines.push(`    <url>${esc(SITE)}/</url>`);
  lines.push(`    <email>${esc(EMAIL)}</email>`);
  lines.push(`    <picture>${esc(SITE)}/favicon.svg</picture>`);
  lines.push('    <description>Справочник вузов России: направления подготовки, ' +
    'формы обучения, стоимость и бюджетные места по официальным данным.</description>');
  lines.push('    <currencies>');
  lines.push('      <currency id="RUR" rate="1"/>');
  lines.push('    </currencies>');
  lines.push('    <offers>');
  for (const o of offers) {
    lines.push(`      <offer id="${esc(o.id)}">`);
    lines.push(`        <name>${esc(o.name)}</name>`);
    lines.push(`        <url>${esc(o.url)}</url>`);
    lines.push(`        <categoryId>${o.categoryId}</categoryId>`);
    lines.push(`        <price>${o.price}</price>`);
    lines.push('        <currencyId>RUR</currencyId>');
    lines.push(`        <description>${esc(o.description)}</description>`);
    // Значения строго из списков Яндекса. Варианта «офлайн» в «Формате обучения»
    // нет вовсе — формат предполагает онлайн; «С преподавателем» ближе всего к
    // обучению в вузе. «Профессия» вместо «Курс», результат — диплом.
    lines.push('        <param name="Формат обучения">С преподавателем</param>');
    lines.push('        <param name="Тип обучения">Профессия</param>');
    lines.push('        <param name="Результат обучения">Диплом</param>');
    lines.push('      </offer>');
  }
  lines.push('    </offers>');
  lines.push('  </shop>');
  lines.push('</yml_catalog>');

  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, lines.join('\n') + '\n', 'utf8');

  const byCat = new Map<number, number>();
  for (const o of offers) byCat.set(o.categoryId, (byCat.get(o.categoryId) ?? 0) + 1);
  console.log(`Фид собран: ${OUT}`);
  console.log(`Предложений: ${offers.length} (лимит ${MAX_OFFERS})`);
  console.log(`Категорий задействовано: ${byCat.size}`);
  if (EMAIL === 'info@vuz-navigator.ru' && !process.env.FEED_EMAIL) {
    console.warn('ВНИМАНИЕ: email в фиде — подстановка по умолчанию. ' +
      'Задайте FEED_EMAIL=<адрес> перед сборкой фида.');
  }
}

main();
