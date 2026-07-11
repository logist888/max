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

export function ldOrg(card: OrgCard, url: string): object {
  const ld: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'CollegeOrUniversity',
    name: card.shortName,
    alternateName: card.fullName,
    url,
  };
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
