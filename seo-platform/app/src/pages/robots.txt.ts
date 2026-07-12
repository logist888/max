import type { APIRoute } from 'astro';

// robots.txt генерируется динамически, чтобы строка Sitemap указывала на
// реальный домен из SITE_URL (та же переменная, что и `site` в конфиге).
// Пока домена нет (site = localhost) — Sitemap не публикуем, но краулинг
// не запрещаем. При смене домена (свой домен вместо pages.dev) файл
// подстраивается сам, править ничего не нужно.
export const GET: APIRoute = ({ site }) => {
  const real = site && site.hostname !== 'localhost';
  const lines = ['User-agent: *', 'Allow: /', ''];
  if (real) lines.push(`Sitemap: ${new URL('sitemap-index.xml', site).href}`, '');
  return new Response(lines.join('\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
