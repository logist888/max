# Канонизация URL и редирект концевого слэша

Сайт собирается с `trailingSlash: 'always'` — канонический адрес всегда
оканчивается на `/` (`/specialnosti/38/`, `/vuz/…-1214/`). Это уже обеспечено:

- **Внутренние ссылки** — все со слэшем (проверка `python3 seo-platform/check_links.py`
  находит 0 ссылок без слэша и 0 битых).
- **`<link rel="canonical">`** на каждой странице указывает на версию со слэшем.
  Даже если поисковик придёт по внешней ссылке без слэша, canonical укажет
  правильный адрес — дублей в индексе не возникнет.
- На локальном статическом сервере запрос без слэша уже отдаёт **301** на версию
  со слэшем (`/specialnosti/38` → `/specialnosti/38/`).

Остаётся гарантировать этот 301 на проде — поведение зависит от хостинга.
Домен и хостинг ещё не выбраны (локальная фаза), поэтому ниже — готовые правила
под типовые варианты. Плюс при деплое задать канонический домен:
`SITE_URL=https://<домен> npx astro build` (иначе canonical ссылается на
`localhost:4321`).

## Nginx

```nginx
# Отдаём каталоги как /path/ и 301-им запрос без слэша.
location / {
    root /var/www/site/dist;
    # Если есть каталог с index.html — добавить слэш (301).
    if (-d $request_filename) { rewrite ^(.*[^/])$ $1/ permanent; }
    try_files $uri $uri/index.html =404;
}
```

## Caddy

```
root * /var/www/site/dist
try_files {path} {path}/index.html
file_server
# Caddy сам не добавляет слэш для каталогов при таком try_files —
# при необходимости включить редирект:
@nodir { not path */ ; not path *.* }
redir @nodir {path}/ 301
```

## Netlify / Cloudflare Pages

«Pretty URLs» включены по умолчанию — запрос без слэша автоматически
301-ится на версию со слэшем. Дополнительная настройка не нужна.
Для явного контроля можно добавить `netlify.toml`:

```toml
[build]
  publish = "seo-platform/app/dist"
[[redirects]]
  from = "/*"
  to = "/:splat/"
  status = 301
  force = false
```

## Проверка после деплоя

```
curl -sI https://<домен>/specialnosti/38   # ожидаем 301 Location: …/38/
curl -sI https://<домен>/specialnosti/38/  # ожидаем 200
python3 seo-platform/check_links.py         # 0 битых, 0 без слэша
```
