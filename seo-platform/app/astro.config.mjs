import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Домен задаётся переменной окружения SITE_URL (на Cloudflare Pages она
// установлена). До появления домена — заглушка localhost, и sitemap не
// генерируется, чтобы не публиковать ссылки на localhost.
const SITE_URL = process.env.SITE_URL;

export default defineConfig({
  site: SITE_URL || 'http://localhost:4321',
  trailingSlash: 'always',
  build: { format: 'directory' },
  // Панель разработчика Astro (Dev Toolbar) — в продакшн-сборке её нет,
  // но и локально в dev она не нужна: выключаем, чтобы не мешала просмотру.
  devToolbar: { enabled: false },
  integrations: [
    // Sitemap строится только при реальном домене. Исключаем noindex-страницы:
    // 404 и пагинацию каталога (/vuzy/2/ и далее) — их канонический адрес это
    // первая страница /vuzy/, в индекс попадать не должны.
    ...(SITE_URL
      ? [sitemap({
          filter: (page) =>
            !/\/404\/?$/.test(page) && !/\/vuzy\/\d+\/?$/.test(page),
        })]
      : []),
  ],
});
