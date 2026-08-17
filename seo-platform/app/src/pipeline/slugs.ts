// Слаги: транслитерация кириллицы + правила этапа 1
// (вуз — транслит короткого имени + id; город/регион — чистый транслит;
// направление — код ОКСО + транслит названия).

const MAP: Record<string, string> = {
  а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', е: 'e', ё: 'e', ж: 'zh', з: 'z',
  и: 'i', й: 'y', к: 'k', л: 'l', м: 'm', н: 'n', о: 'o', п: 'p', р: 'r',
  с: 's', т: 't', у: 'u', ф: 'f', х: 'h', ц: 'ts', ч: 'ch', ш: 'sh',
  щ: 'sch', ъ: '', ы: 'y', ь: '', э: 'e', ю: 'yu', я: 'ya',
};

export function translit(text: string): string {
  return text
    .toLowerCase()
    .split('')
    .map((ch) => MAP[ch] ?? ch)
    .join('');
}

export function slugify(text: string): string {
  return translit(text)
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-{2,}/g, '-');
}

/** Слаг вуза: читаемая часть + id источника (уникальность и устойчивость). */
export function orgSlug(shortName: string, id: string): string {
  const base = slugify(shortName).slice(0, 60).replace(/-+$/, '');
  return base ? `${base}-${id}` : `vuz-${id}`;
}

/** Слаг направления: код ОКСО (точки в дефисы) + название. */
export function directionSlug(okso: string, name: string): string {
  const code = okso.replace(/^\d+\./, '').replace(/\./g, '-');
  const base = slugify(name).slice(0, 50).replace(/-+$/, '');
  return base ? `${code}-${base}` : code;
}
