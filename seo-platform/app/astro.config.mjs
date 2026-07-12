import { defineConfig } from 'astro/config';

// Домена пока нет (решение владельца: локальная фаза). SITE_URL задаётся
// переменной окружения при появлении домена; до этого — заглушка, sitemap
// не генерируется.
export default defineConfig({
  site: process.env.SITE_URL || 'http://localhost:4321',
  trailingSlash: 'always',
  build: { format: 'directory' },
  // Панель разработчика Astro (Dev Toolbar) — в продакшн-сборке её нет,
  // но и локально в dev она не нужна: выключаем, чтобы не мешала просмотру.
  devToolbar: { enabled: false },
});
