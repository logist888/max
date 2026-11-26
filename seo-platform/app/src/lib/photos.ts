// Фотографии вузов. Два источника, поле src в карте соответствий.
//
// src = "commons" (или поле отсутствует — так записаны первые снимки):
// Викисклад. У каждого файла явная свободная лицензия и указан автор. Условие
// лицензий CC BY / CC BY-SA / FAL — указание автора и лицензии рядом с
// изображением, поэтому страница вуза рисует подпись: автор, лицензия, ссылка
// на файл. Вуз и снимок сопоставлены по домену официального сайта через
// Викиданные — проверяемая привязка.
//
// src = "vuzopedia": снимки с vuzopedia.ru. Решение о публикации и юридическая
// сторона — на владельце проекта (26.11.2026). Автора и лицензии у этих снимков
// нет, поэтому подписи под ними нет, а license и acquireLicensePage в
// разметке не заполняются. Ссылки на официальный сайт на карточках Vuzopedia
// тоже нет, так что пары «вуз — снимок» сопоставлены по полному названию и
// городу и прошли ручную сверку; сомнительные отложены.
//
// Только головные вузы: филиалу здание головного вуза не принадлежит. Карта
// лежит в data/photos/vuz-photos.json.

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

export type PhotoSource = 'commons' | 'vuzopedia';

export interface VuzPhoto {
  /** Откуда снимок. Отсутствие поля означает Викисклад — так записаны первые. */
  src?: PhotoSource;
  file: string;
  /** Превью для списков, 192×144. Делает scripts/photos/make_thumbs.py. */
  thumb?: string;
  file360: string;
  width: number;
  height: number;
  caption: string;
  author: string;
  licence: string;
  licenceUrl: string;
  source: string;
  wikidata: string;
}

let cache: Record<string, VuzPhoto> | null = null;

export function vuzPhotos(): Record<string, VuzPhoto> {
  if (cache) return cache;
  try {
    cache = JSON.parse(
      readFileSync(resolve(process.cwd(), '../data/photos/vuz-photos.json'), 'utf8'),
    ) as Record<string, VuzPhoto>;
  } catch {
    // Фотографий может не быть вовсе — сайт должен собираться и без них.
    cache = {};
  }
  return cache!;
}

export function vuzPhoto(slug: string): VuzPhoto | undefined {
  return vuzPhotos()[slug];
}

/** Снимок с Викисклада — у него есть автор и лицензия, их надо показать. */
export function isCommons(photo: VuzPhoto): boolean {
  return (photo.src ?? 'commons') === 'commons';
}

// Мусор, которым Викисклад помечает кадры в серии: «СибУПК 03», «(04)»,
// «Корпус № 5», «РосНОУ 20220810 102124», дата съёмки, имя файла с камеры.
// Для альта это шум, и его срезаем по кругу, пока строка не перестанет меняться.
const TRIM: RegExp[] = [
  /[\s.,;:·—–_«»"'-]+$/,
  /[\s(]*№\s*\)?$/,
  /[\s·—–-]*\(?\d[\d\s.:-]*\)?$/,
  /[.,;\s]*\(?(?:\d{1,2}\s+)?[а-яё]+\s+\d{4}(?:\s+года)?\)?$/i,
  /[,\s]*фото$/i,
  /\s+[a-zа-яё]$/,
];
const CAM_FILE = /^(?:DSC|DSCN|IMG|IMGP|P|PICT)[\s_]*\d+[\s_]*(?:\d{4}[\s_]*)?/i;
// Подпись годится в альт, только если она называет снятый объект, а не просто
// повторяет название вуза и не рассказывает сюжет («Осмотр центра искусств»).
const OBJECT = /корпус|здание|кампус|фасад|\bвид\b/i;
// Организационно-правовая шелуха в названии: в подписи её никогда нет, и для
// проверки «назван ли вуз» она бесполезна.
const LEGAL_NOISE = new Set([
  'фгбоу', 'фгаоу', 'фгкоу', 'фгбну', 'гбоу', 'гаоу', 'гкоу', 'ано', 'чоу', 'ноу',
  'оу', 'бу', 'во', 'имени', 'россии', 'российской', 'федерации', 'минздрава',
]);

/** Альтернативный текст фотографии.
 *
 *  Подпись Викисклада берём, только если выполнено всё: она по-русски, говорит,
 *  что в кадре («главный корпус», «вид», «здание»), и сама называет вуз.
 *  Половина подписей там латиницей или вида «Sibup hull», часть описывает сюжет
 *  («Осмотр центра искусств»), часть — безымянный «Учебно-лабораторный корпус»:
 *  такой альт хуже отсутствия. Во всех остальных случаях — название вуза и
 *  город; для фотографии объекта это обычная практика. Слова «фотография» и
 *  «изображение» в альт не пишем, их читает сам скринридер.
 *
 *  Вуз считается названным, если подпись содержит аббревиатуру или начало
 *  значимого слова из названия: по-русски слова склоняются («Московского
 *  политехнического»), поэтому сверяем по первым пяти буквам, а не целиком. */
export function photoAltText(
  photo: VuzPhoto, shortName: string, cityName: string, acronyms: string[] = [],
): string {
  const title = (shortName.split(',')[0] ?? '').trim() || shortName;
  const plain = `${title}, ${cityName}`;

  let c = (photo.caption || '').trim().replace(CAM_FILE, '').trim();
  for (let i = 0; i < 6; i++) {
    const before = c;
    for (const re of TRIM) c = c.replace(re, '').trim();
    if (c === before) break;
  }
  const usable = /[А-Яа-яЁё]/.test(c) && c.length >= 12 && c.length <= 140
    && c.includes(' ') && OBJECT.test(c);
  if (!usable) return plain;

  const low = c.toLowerCase();
  const stems = title
    .split(/[\s,.]+/)
    .map((w) => w.replace(/[«»"'()]/g, '').toLowerCase())
    .filter((w) => w.length >= 5 && !LEGAL_NOISE.has(w))
    .map((w) => w.slice(0, 5));
  const short = acronyms.filter((a) => a.length >= 3).map((a) => a.toLowerCase());
  const named = stems.some((s) => low.includes(s)) || short.some((a) => low.includes(a));
  if (!named) return plain;

  return low.includes(cityName.toLowerCase().slice(0, 6)) ? c : `${c}, ${cityName}`;
}
