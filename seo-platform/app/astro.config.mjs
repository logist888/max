import { defineConfig } from 'astro/config';

// Домена пока нет (решение владельца: локальная фаза). SITE_URL задаётся
// переменной окружения при появлении домена; до этого — заглушка, sitemap
// не генерируется.
export default defineConfig({
  site: process.env.SITE_URL || 'http://localhost:4321',
  trailingSlash: 'always',
  build: { format: 'directory' },
});
