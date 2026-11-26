# Публикация на Cloudflare Pages

Бесплатно, работает напрямую с приватным репозиторием `logist888/max`
(публиковать конфиденциальный контекст MainExperts не требуется). Сайт
раздаётся с корня домена — в коде ничего переписывать не нужно.

## Что уже готово в репозитории

- `seo-platform/app/package.json` → скрипт `npm run site` (генерация витрин
  из снимка базы + сборка Astro одной командой).
- `seo-platform/app/.nvmrc` → Node 22.12.0 (Astro 7 требует ≥22.12; Cloudflare
  читает `.nvmrc` из root directory автоматически).
- Снимок базы `seo-platform/data/universities_2026-07-10.json.gz` — в репозитории,
  поэтому сборка на стороне Cloudflare самодостаточна.

## Шаги (делает владелец, ~5 минут)

1. Зайти на **dash.cloudflare.com** (или зарегистрироваться — бесплатно) →
   раздел **Workers & Pages** → **Create** → вкладка **Pages** →
   **Connect to Git**.
2. Авторизовать GitHub, выбрать репозиторий **logist888/max**.
3. **Production branch:** ветка, где лежит платформа —
   `claude/education-seo-platform-p5k4i8` (или основная, если код туда смёржен).
4. В **Build settings** задать вручную (фреймворк-пресет можно не выбирать):
   - **Root directory:** `seo-platform/app`
   - **Build command:** `npm run site`
   - **Build output directory:** `dist`
5. **Save and Deploy.** Первая сборка идёт ~2–4 минуты. По завершении сайт
   доступен по адресу вида `https://<имя-проекта>.pages.dev`.

## После первого деплоя — включить правильный canonical

Пока адрес сайта неизвестен, `<link rel="canonical">` указывает на
`localhost`. Чтобы он указывал на реальный адрес:

1. В проекте Pages → **Settings** → **Variables and Secrets** →
   добавить переменную сборки **`SITE_URL`** со значением
   `https://<имя-проекта>.pages.dev` (или свой домен, если подключишь).
2. **Retry deployment** (пересобрать) — canonical и Open Graph станут
   указывать на боевой адрес.

## Автообновление

Cloudflare пересобирает сайт при каждом push в production-branch — отдельный
CI настраивать не нужно. Когда летом 2027 появится новый снимок базы,
достаточно заменить файл в `seo-platform/data/`, обновить путь в
`src/pipeline/run.ts` и запушить — сайт пересоберётся сам.

## Проверки

- Концевой слэш: Cloudflare Pages сам редиректит `/specialnosti/38` →
  `/specialnosti/38/` (308) при наличии `…/38/index.html` — совпадает с
  `trailingSlash: 'always'`.
- Размер: 9 523 файла (лимит Cloudflare — 20 000), крупнейший 616 КБ
  (лимит — 25 МБ на файл). С запасом.
- Свой домен подключается в **Custom domains** (нужен купленный домен;
  тогда `SITE_URL` меняется на него).
