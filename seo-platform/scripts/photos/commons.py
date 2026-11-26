"""Фотографии вузов с Викисклада (Wikimedia Commons).

У каждого файла свободная лицензия и указан автор; они собираются в карту
соответствий. Показывать ли их на сайте, решает SHOW_PHOTO_CREDITS в
app/src/lib/photos.ts — сейчас выключено решением владельца проекта. Снимки с сайтов самих
вузов не берутся: это чужие произведения.

  python3 scripts/photos/commons.py            # найти и скачать
  python3 scripts/photos/commons.py --dry-run  # только показать, что найдётся
  python3 scripts/photos/make_thumbs.py        # превью для списков

Привязка вуз → снимок проверяемая, через Викиданные:
  1. объект Викиданных с тем же доменом официального сайта (P856);
  2. если совпал только регистрируемый домен (spbu.ru против english.spbu.ru),
     дополнительно сверяются название и город — иначе на общий хостинг
     садятся чужие организации («АНО ВПО ПСИ» → «Лицей № 1»).

Файл берётся в таком порядке: картинка объекта (P18), заглавная картинка
статьи русской Википедии, первый подходящий файл категории Викисклада.
Логотипы, гербы и векторные знаки выбрасываются: это не фотография, а
логотип ещё и товарный знак. Граница слова при этом обязательна —
«Вологодской» содержит «олого».

Скачивается превью СТАНДАРТНОЙ ширины, 960 px. Викимедиа отдаёт из кэша
только ступени 20, 40, 60, 120, 250, 330, 500, 960, 1280, 1920, 3840; любую
другую ширину нарезает на лету и за это режет частоту запросов (429).
"""
import argparse, hashlib, html, json, pathlib, re, sys, time, urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import (PHOTOS, city_key, convert, domain, fetch, head_without_photo,
                    load_manifest, load_orgs, save_manifest)

SPARQL = '''
SELECT ?u ?uLabel ?site ?img ?cat ?ruwiki ?placeLabel WHERE {
  ?u wdt:P31/wdt:P279* wd:Q2385804 .
  ?u wdt:P17 wd:Q159 .
  ?u wdt:P856 ?site .
  OPTIONAL { ?u wdt:P18 ?img }
  OPTIONAL { ?u wdt:P373 ?cat }
  OPTIONAL { ?u wdt:P131 ?place }
  OPTIONAL { ?ruwiki schema:about ?u ; schema:isPartOf <https://ru.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ru,en" }
}'''
STEPS = [20, 40, 60, 120, 250, 330, 500, 960, 1280, 1920, 3840]
WEB_IMG = ('.jpg', '.jpeg', '.png', '.webp')
OK_LICENCE = re.compile(r'^(cc[\s-]|cc0|public domain|pd|gfdl|fal)', re.I)
LOGO = re.compile(r'(?<![а-яёa-z])(логотип\w*|лого(?![а-яё])|герб\w*|эмблем\w*|emblem\w*|'
                  r'coat.of.arms|значок)|(?<![a-z])logo|LOGO', re.I)
STOP = {'инстит', 'универ', 'академ', 'госуда', 'федера', 'высшег', 'образо', 'учрежд', 'бюджет',
        'автоно', 'некомм', 'органи', 'профес', 'россий', 'имени', 'научно', 'учебны', 'национ'}


def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def stems(s):
    return {w[:6] for w in re.split(r'[^А-Яа-яЁёA-Za-z]+', s.lower()) if len(w) >= 5 and w[:6] not in STOP}


def registrable(h):
    p = h.split('.')
    if len(p) >= 3 and p[-2] in ('com', 'org', 'net', 'edu', 'gov', 'ac', 'co'):
        return '.'.join(p[-3:])
    return '.'.join(p[-2:])


def api(host, params, tries=5):
    params = dict(params, format='json')
    body = urllib.parse.urlencode(params).encode()
    return json.loads(fetch(f'https://{host}/w/api.php', data=body, pause=8, tries=tries))


def wikidata():
    body = urllib.parse.urlencode({'query': SPARQL}).encode()
    raw = fetch('https://query.wikidata.org/sparql', data=body, pause=10)
    # SPARQL по POST отвечает JSON, если попросить; по умолчанию — XML.
    if raw.lstrip().startswith(b'<'):
        raw = fetch('https://query.wikidata.org/sparql?format=json&' +
                    urllib.parse.urlencode({'query': SPARQL}), pause=10)
    rows = json.loads(raw)['results']['bindings']
    v = lambda r, k: r.get(k, {}).get('value', '')
    return [{'q': v(r, 'u').rsplit('/', 1)[-1], 'label': v(r, 'uLabel'), 'site': v(r, 'site'),
             'img': v(r, 'img'), 'cat': v(r, 'cat'), 'ru': v(r, 'ruwiki'), 'place': v(r, 'placeLabel')}
            for r in rows]


def link(orgs, items):
    """Вуз → объект Викиданных. Точный домен — сразу; регистрируемый домен —
    только при совпадении названия и города."""
    exact, loose = {}, {}
    for it in items:
        d = domain(it['site'])
        exact.setdefault(d, it)
        loose.setdefault(registrable(d), []).append(it)
    out = {}
    for o in orgs:
        hit = next((exact[domain(s)] for s in o['sites'] if domain(s) in exact), None)
        if not hit:
            for s in o['sites']:
                for it in loose.get(registrable(domain(s)), []):
                    common = (stems(o['full']) | stems(o['short'])) & stems(it['label'])
                    same_city = not it['place'] or city_key(o['city'])[:5] in city_key(it['place']) \
                        or city_key(it['place']) in city_key(o['city'])
                    if len(common) >= 2 and same_city:
                        hit = it
                        break
                if hit:
                    break
        if hit:
            out[o['slug']] = hit
    return out


def pick_file(it):
    """(имя файла на Викискладе | None, источник или причина отказа).

    Источник, который не ответил (Википедия охотно отдаёт 429 с общего
    адреса), пропускается, а не роняет прогон: следующий заход его доберёт.
    """
    if it['img']:
        f = 'File:' + urllib.parse.unquote(it['img'].rsplit('/', 1)[-1]).replace('_', ' ')
        # Только растровые веб-форматы: у TIFF и PDF превью лежит по другому
        # адресу (lossy-page1-…), а SVG — почти всегда логотип или схема.
        if not LOGO.search(f) and f.lower().endswith(WEB_IMG):
            return f, 'P18'
    failed = []
    if it['ru']:
        title = urllib.parse.unquote(it['ru'].rsplit('/', 1)[-1]).replace('_', ' ')
        try:
            d = api('ru.wikipedia.org', {'action': 'query', 'prop': 'pageimages', 'piprop': 'name',
                                         'titles': title}, tries=3)
        except Exception:
            failed.append('Википедия не ответила')
        else:
            for p in (d.get('query', {}).get('pages') or {}).values():
                nm = p.get('pageimage')
                if nm and not LOGO.search(nm) and nm.lower().endswith(WEB_IMG):
                    return 'File:' + nm.replace('_', ' '), 'статья Википедии'
    if it['cat']:
        try:
            d = api('commons.wikimedia.org', {'action': 'query', 'list': 'categorymembers', 'cmtype': 'file',
                                              'cmtitle': 'Category:' + it['cat'], 'cmlimit': '30'}, tries=3)
        except Exception:
            failed.append('Викисклад не ответил')
        else:
            for c in d.get('query', {}).get('categorymembers', []):
                t = c['title']
                if t.lower().endswith(WEB_IMG) and not LOGO.search(t):
                    return t, 'категория Викисклада'
    return None, ', '.join(failed) or 'подходящего файла нет'


def rights(files):
    out = {}
    names = sorted(set(files))
    for i in range(0, len(names), 20):
        try:
            d = api('commons.wikimedia.org', {'action': 'query', 'prop': 'imageinfo',
                                              'iiprop': 'extmetadata|size', 'titles': '|'.join(names[i:i + 20])})
        except Exception as e:
            # Без сведений о правах файл не ставится — пачка просто пропускается.
            print(f'  сведения о правах для пачки {i // 20 + 1} не получены: {e}', flush=True)
            continue
        for p in (d.get('query', {}).get('pages') or {}).values():
            ii = (p.get('imageinfo') or [{}])[0]
            out[p.get('title', '')] = {'meta': {k: v.get('value') for k, v in (ii.get('extmetadata') or {}).items()},
                                       'width': ii.get('width') or 0}
        time.sleep(3)
    return out


def thumb_url(file_title, width):
    name = file_title[len('File:'):].replace(' ', '_')
    h = hashlib.md5(name.encode('utf-8')).hexdigest()
    q = urllib.parse.quote(name)
    w = max([s for s in STEPS if s <= 960 and (not width or s < width)] or [0])
    if not w:
        return f'https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{q}'
    return f'https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{w}px-{q}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=0, help='не больше N вузов (для проверки)')
    a = ap.parse_args()

    manifest = load_manifest()
    need = head_without_photo(load_orgs(), manifest)
    print('головных вузов без фото:', len(need), flush=True)
    items = wikidata()
    print('объектов в Викиданных:', len(items), flush=True)
    linked = link(need, items)
    print('привязано к Викиданным:', len(linked), flush=True)

    picks, why = {}, {}
    for slug, it in list(linked.items())[: a.limit or None]:
        f, how = pick_file(it)
        if f:
            picks[slug] = (f, it['q'])
        why[how] = why.get(how, 0) + 1
        time.sleep(1)
    print('найден файл:', len(picks), flush=True)
    for k, v in sorted(why.items(), key=lambda kv: -kv[1]):
        print(f'   {v:4}  {k}')
    if a.dry_run:
        for s, (f, q) in list(picks.items())[:20]:
            print(f'   {s} → {f}')
        return

    info = rights([f for f, _ in picks.values()])
    done = skipped = 0
    for slug, (f, q) in picks.items():
        rec = info.get(f) or {}
        m = rec.get('meta') or {}
        lic, author = clean(m.get('LicenseShortName')), clean(m.get('Artist'))
        if not lic or not OK_LICENCE.match(lic):
            skipped += 1
            continue
        if not author and not re.match(r'^(public domain|pd|cc0)', lic, re.I):
            skipped += 1          # CC BY / BY-SA без автора публиковать нельзя
            continue
        src = PHOTOS / f'{slug}.src'
        try:
            src.write_bytes(fetch(thumb_url(f, rec.get('width')), pause=15))
            w, h = convert(src, slug, crop_4x3=False)
        except Exception as e:
            print(f'  {slug}: {e}', flush=True)
            skipped += 1
            continue
        finally:
            src.unlink(missing_ok=True)
        name = f[len('File:'):].replace(' ', '_')
        manifest[slug] = {
            'src': 'commons', 'file': f'/photos/{slug}.webp', 'file360': f'/photos/{slug}-360.webp',
            'width': w, 'height': h,
            'caption': (clean(m.get('ObjectName')) or clean(m.get('ImageDescription')))[:180],
            'author': author[:160], 'licence': lic[:60], 'licenceUrl': clean(m.get('LicenseUrl')),
            'source': 'https://commons.wikimedia.org/wiki/File:' + urllib.parse.quote(name),
            'wikidata': q}
        done += 1
        if done % 10 == 0:
            save_manifest(manifest)
        time.sleep(2)
    save_manifest(manifest)
    print(f'скачано: {done} | отброшено: {skipped} | в карте всего: {len(manifest)}')
    print('дальше: python3 scripts/photos/make_thumbs.py')


if __name__ == '__main__':
    main()
