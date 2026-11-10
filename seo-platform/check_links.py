# -*- coding: utf-8 -*-
"""Проверка ссылок собранного сайта (регресс перед деплоем).

Проходит по всем HTML в dist/ и проверяет каждую внутреннюю ссылку:
  • не ведёт ли она в никуда (битая ссылка);
  • оканчивается ли на «/» (канонический вид при trailingSlash: 'always').

Запуск: python3 seo-platform/check_links.py [путь к dist]
Код возврата 1, если найдены битые или неканонические ссылки.
"""
import collections
import os
import re
import sys

DIST = sys.argv[1] if len(sys.argv) > 1 else "seo-platform/app/dist"
HREF = re.compile(r'href="(/[^"#?]*)"')


def target_exists(path):
    full = os.path.join(DIST, path.lstrip("/"))
    if path.endswith("/"):
        return os.path.isfile(os.path.join(full, "index.html"))
    return os.path.isfile(full) or os.path.isfile(os.path.join(full, "index.html"))


def main():
    pages = [os.path.join(r, f)
             for r, _, fs in os.walk(DIST) for f in fs if f.endswith(".html")]
    if not pages:
        print(f"Нет HTML в {DIST} — сначала npx astro build")
        return 1
    print(f"HTML-страниц: {len(pages)}")

    broken = collections.Counter()
    no_slash = collections.Counter()
    seen = set()
    total = 0
    for pg in pages:
        for m in HREF.finditer(open(pg, encoding="utf-8").read()):
            h = m.group(1)
            total += 1
            # пропускаем ассеты (статические каталоги и файлы с расширением)
            if h.startswith(("/_astro/", "/fonts/")) or "." in h.rsplit("/", 1)[-1]:
                continue
            if h in seen:
                continue
            seen.add(h)
            if not target_exists(h):
                broken[h] += 1
            if not h.endswith("/"):
                no_slash[h] += 1

    print(f"Всего href: {total}, уникальных внутренних: {len(seen)}")
    print(f"Битых ссылок: {len(broken)} | без концевого слэша: {len(no_slash)}")
    for h in list(broken)[:20]:
        print(f"  БИТАЯ: {h}")
    for h in list(no_slash)[:20]:
        print(f"  БЕЗ СЛЭША: {h}")
    return 1 if (broken or no_slash) else 0


if __name__ == "__main__":
    sys.exit(main())
