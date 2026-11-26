// Фотографии вузов с Викисклада.
//
// Почему именно оттуда: у каждого файла есть явная свободная лицензия и указан
// автор. Снимки с сайтов самих вузов — чужие произведения, публиковать их без
// лицензии нельзя, поэтому они не используются.
//
// Условие лицензий CC BY / CC BY-SA / FAL — указание автора и лицензии рядом с
// изображением. Поэтому компонент на странице вуза обязан рисовать подпись:
// автор, название лицензии и ссылка на файл-источник.
//
// Соответствие вуз → фотография строится по совпадению домена официального
// сайта с Викиданными (надёжный признак), и только для головных вузов: филиалу
// здание головного вуза не принадлежит. Карта собирается скриптом и лежит в
// data/photos/vuz-photos.json.

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

export interface VuzPhoto {
  file: string;
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
