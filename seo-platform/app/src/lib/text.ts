// Текстовый слой: форматирование, склонения, автогенерация мета-текстов,
// FAQ и JSON-LD — только из фактов витрин (этап 2). Нет данных — фраза
// выпадает целиком.

import type { CostRange, OrgCard } from './data.ts';

export function plural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}

export function rub(n: number): string {
  return `${n.toLocaleString('ru-RU')} ₽`;
}

export function costPhrase(range: CostRange | null): string | null {
  if (!range) return null;
  return range.min === range.max
    ? `${rub(range.min)} в год`
    : `от ${rub(range.min)} до ${rub(range.max)} в год`;
}

export function orgTitle(card: OrgCard): string {
  return `${card.shortName} — программы, стоимость, общежитие | ${card.cityName}`;
}

export function orgDescription(card: OrgCard, campaign: string): string {
  const parts: string[] = [];
  parts.push(`${card.shortName} (${card.cityName})`);
  if (card.directionsCount > 0) {
    parts.push(`${card.directionsCount} ${plural(card.directionsCount,
      'направление подготовки', 'направления подготовки', 'направлений подготовки')}`);
  }
  if (card.hasBudget) parts.push('есть бюджетные места');
  const cost = costPhrase(card.costRange);
  if (cost) parts.push(`платное обучение ${cost}`);
  if (card.dormitory) parts.push('общежитие');
  if (card.militaryDept) parts.push('военная кафедра');
  parts.push(`приём ${campaign}`);
  return parts.join('. ') + '.';
}

export interface FaqItem { q: string; a: string }

export function orgFaq(card: OrgCard, snapshotDate: string): FaqItem[] {
  const faq: FaqItem[] = [];
  faq.push({
    q: `Есть ли бюджетные места в ${card.shortName}?`,
    a: card.hasBudget
      ? 'Да, в выгрузке заявлены бюджетные места (основные места в рамках КЦП и квоты).'
      : `В выгрузке от ${snapshotDate} бюджетные места не указаны.`,
  });
  const cost = costPhrase(card.costRange);
  if (cost) {
    faq.push({ q: 'Сколько стоит платное обучение?', a: `По данным выгрузки — ${cost}.` });
  }
  faq.push({
    q: 'Есть ли общежитие?',
    a: card.dormitory
      ? card.dormPlaces
        ? `Да. Мест в общежитии по данным выгрузки: ${card.dormPlaces}.`
        : 'Да, общежитие заявлено. Число мест в выгрузке не указано.'
      : `В выгрузке от ${snapshotDate} общежитие не указано.`,
  });
  if (card.militaryDept) {
    faq.push({ q: 'Есть ли военная кафедра?', a: 'Да, военный учебный центр заявлен в данных.' });
  }
  return faq;
}

export function directionFaq(
  d: { name: string; orgCount: number; cityCount: number; hasBudget: boolean; costRange: CostRange | null },
  snapshotDate: string,
): FaqItem[] {
  const faq: FaqItem[] = [];
  faq.push({
    q: `В скольких вузах есть направление «${d.name}»?`,
    a: `По выгрузке — ${d.orgCount} ${plural(d.orgCount, 'вуз', 'вуза', 'вузов')} в ${d.cityCount} ${plural(d.cityCount, 'городе', 'городах', 'городах')}.`,
  });
  faq.push({
    q: 'Есть ли бюджетные места по этому направлению?',
    a: d.hasBudget
      ? 'Да, в выгрузке заявлены бюджетные места хотя бы в одном вузе.'
      : `В выгрузке от ${snapshotDate} бюджетные места не указаны.`,
  });
  const cost = costPhrase(d.costRange);
  if (cost) faq.push({ q: 'Сколько стоит платное обучение?', a: `По данным выгрузки — ${cost}.` });
  return faq;
}

// FAQ для комбо «направление × город/регион»: place — уже склонённое имя
// места («в Москве», «в Московской области»), считанное из данных.
export function placeDirectionFaq(
  dirName: string, placeQuestion: string, orgCount: number,
  budget: boolean, range: CostRange | null, snapshotDate: string,
): FaqItem[] {
  const faq: FaqItem[] = [];
  faq.push({
    q: `Сколько вузов по направлению «${dirName}» ${placeQuestion}?`,
    a: `${orgCount} ${plural(orgCount, 'вуз', 'вуза', 'вузов')} по выгрузке.`,
  });
  faq.push({
    q: 'Есть ли бюджетные места?',
    a: budget
      ? 'Да, бюджетные места заявлены хотя бы в одном вузе.'
      : `В выгрузке от ${snapshotDate} бюджетные места не указаны.`,
  });
  const cost = costPhrase(range);
  if (cost) faq.push({ q: 'Сколько стоит платное обучение?', a: `По данным выгрузки — ${cost}.` });
  return faq;
}

// ---- JSON-LD

export function ldBreadcrumbs(items: { name: string; url: string }[]): object {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((it, i) => ({
      '@type': 'ListItem', position: i + 1, name: it.name, item: it.url,
    })),
  };
}

/** Фотография как schema.org ImageObject.
 *
 *  Не просто адрес файла: у снимков с Викисклада есть автор и лицензия, и
 *  разметка — то место, где робот их видит. Свойства license и
 *  acquireLicensePage поисковики читают как сведения о правах на изображение;
 *  creditText — подпись, которую можно показать рядом со снимком. Указание
 *  автора и лицензии и так обязательно по CC BY / CC BY-SA, разметка его
 *  дублирует машинно. */
export function ldImage(opts: {
  url: string; url360?: string; width: number; height: number;
  alt: string; author?: string; licenceUrl?: string; source?: string;
}): object {
  const ld: Record<string, unknown> = {
    '@type': 'ImageObject',
    contentUrl: opts.url,
    url: opts.url,
    width: opts.width,
    height: opts.height,
    caption: opts.alt,
  };
  if (opts.url360) ld['thumbnailUrl'] = opts.url360;
  // Автора отдаём текстом. Типизировать его как Person нельзя: в поле Artist на
  // Викискладе бывает и организация, и несколько человек, и ник — тип был бы
  // домыслом.
  if (opts.author) {
    ld['creditText'] = opts.author;
    ld['copyrightNotice'] = opts.author;
  }
  if (opts.licenceUrl) ld['license'] = opts.licenceUrl;
  if (opts.source) ld['acquireLicensePage'] = opts.source;
  return ld;
}

export function ldOrg(card: OrgCard, url: string, image?: string | object): object {
  const ld: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'CollegeOrUniversity',
    name: card.shortName,
    alternateName: card.fullName,
    url,
  };
  // Фотография — абсолютный адрес: поисковику относительный путь бесполезен.
  if (image) ld['image'] = image;
  if (card.websites[0]) ld['sameAs'] = card.websites;
  if (card.address) {
    ld['address'] = { '@type': 'PostalAddress', streetAddress: card.address };
  }
  return ld;
}

export function ldFaq(faq: FaqItem[]): object {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faq.map((f) => ({
      '@type': 'Question',
      name: f.q,
      acceptedAnswer: { '@type': 'Answer', text: f.a },
    })),
  };
}

/** Программа обучения как schema.org EducationalOccupationalProgram — для страницы
 *  направления. Это точный тип для программы высшего образования: уровень, формы,
 *  стоимость, код ОКСО. Яндексу и Google разметка видна сразу, фид и модерация
 *  для неё не нужны.
 *
 *  Выдаём только то, что есть в выгрузке. Провайдера нет намеренно: на странице
 *  направления вузов много, а свойство provider одно — указывать один вуз из
 *  сотни было бы выдумкой. Длительность обучения и профессии после выпуска тоже
 *  не выдаём: длительности в данных нет, а связь с профессиями у нас экспертная,
 *  не официальная, и в разметке выглядела бы как факт.
 *
 *  Стоимость — за учебный год, а не за программу целиком, поэтому цена идёт через
 *  UnitPriceSpecification с явной единицей: иначе робот прочитает годовую цену как
 *  полную стоимость обучения. */
export function ldProgram(opts: {
  name: string; okso: string; level: string; url: string;
  costRange: CostRange | null; forms: string[]; orgCount: number; hasBudget: boolean;
}): object {
  const ld: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'EducationalOccupationalProgram',
    name: opts.name,
    identifier: oksoCode(opts.okso),
    programType: opts.level,
    educationalLevel: opts.level,
    url: opts.url,
    inLanguage: 'ru',
  };
  if (opts.forms.length) ld['educationalProgramMode'] = opts.forms;
  if (opts.costRange) {
    ld['offers'] = {
      '@type': 'AggregateOffer',
      priceCurrency: 'RUB',
      lowPrice: opts.costRange.min,
      highPrice: opts.costRange.max,
      offerCount: opts.orgCount,
      category: 'Платное обучение',
      priceSpecification: {
        '@type': 'UnitPriceSpecification',
        priceCurrency: 'RUB',
        minPrice: opts.costRange.min,
        maxPrice: opts.costRange.max,
        unitText: 'учебный год',
        referenceQuantity: { '@type': 'QuantitativeValue', value: 1, unitText: 'учебный год' },
      },
    };
  }
  if (opts.hasBudget) ld['financialAidEligible'] = 'Бюджетные места (КЦП и квоты)';
  return ld;
}

/** Код специальности для показа человеку.
 *
 *  В выгрузке код записан как «<область образования>.<код>»: у ФГОС это
 *  6.44.03.05 → 44.03.05, где первая цифра — служебная область (по 56 УГСН из 57
 *  она однозначна и ничего не теряет). Но у научных специальностей код сам по себе
 *  трёхчастный: 3.1.7 «Стоматология» — это отрасль 3 (медицинские науки), группа
 *  3.1 (клиническая медицина), специальность 3.1.7. Срез первой цифры превращал его
 *  в «1.7» — такого кода в номенклатуре нет (в группе 1 только 1.1–1.6).
 *
 *  Поэтому режем только четырёхчастные коды ФГОС, трёхчастные научные оставляем
 *  целиком. */
export function oksoCode(okso: string): string {
  return okso.split('.').length === 4 ? okso.replace(/^\d+\./, '') : okso;
}
