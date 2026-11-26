"""Фотографии вузов с vuzopedia.ru.

Решение о публикации и юридическая сторона — на владельце проекта
(26.11.2026). Под этими снимками нет подписи с автором и лицензией, в
разметке у них не заполняются license и acquireLicensePage: автора и
лицензии у них нет. Это делает сайт по полю src: "vuzopedia".

Три шага, каждый можно повторять:

  python3 scripts/photos/vuzopedia.py crawl     # обойти каталог Vuzopedia
  python3 scripts/photos/vuzopedia.py match     # подобрать снимки, отсеять мусор
  python3 scripts/photos/vuzopedia.py install   # поставить отобранное
  python3 scripts/photos/make_thumbs.py         # превью для списков

match оставляет лист для просмотра глазами (data/photos/review/sheet.jpg):
заглушки и логотипы скрипт отсеивает сам, а рекламные баннеры и картинки
вместо фото — только человек. Номера плохих кадров передаются install через
--reject, и они запоминаются в rejected.json, чтобы не всплывать снова.

Со временем Vuzopedia заменяет заглушки настоящими фото — тогда повторный
crawl + match найдёт их, а на сайте заглушка в списке сменится на снимок.

ПРАВИЛО СОПОСТАВЛЕНИЯ (владельца проекта): совпадает город И (аббревиатура
ИЛИ полное название) — значит, это тот же вуз. Ссылки на официальный сайт на
карточках Vuzopedia нет, так что проверить по домену нечем. Уточнения, без
которых правило ломается:
  - город сравнивается целиком, не по началу слова;
  - из аббревиатур выброшены организационно-правовая часть (ФГБОУ, ВО, АНО),
    общие хвосты (РАН, РФ, Минздрава), сокращения городов (СПб) и пометки
    ведомств (ДЗМ): по ним совпали бы десятки разных учреждений;
  - если аббревиатура в городе принадлежит нескольким карточкам — это
    неоднозначность, решения нет;
  - одна карточка Vuzopedia не может достаться двум нашим вузам.
Проверено 26.11.2026 на ручной разметке: на 263 верных парах правило дало ту
же карточку в 244, ни одной чужой; на 64 заведомо неверных — ни одного
совпадения.
"""
import argparse, html, json, pathlib, re, shutil, subprocess, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import (DATA, PHOTOS, UA_BROWSER, city_key, convert, fetch, head_without_photo,
                    load_manifest, load_orgs, save_manifest, sig_distance, signature)

CARDS = DATA / 'vuzopedia-cards.json'
CANDIDATES = DATA / 'review' / 'candidates.json'
REJECTED = DATA / 'vuzopedia-rejected.json'
STUB = DATA / 'vuzopedia-stub.sig'          # отпечаток заглушки Vuzopedia
REVIEW = DATA / 'review'
STUB_LIMIT = 12.0     # у заглушки с собой 0, у настоящих фото от 38 и выше

# ---------------------------------------------------------------- обход

CARD = re.compile(
    r'class="vxVuzPrime__card".*?data-src="(?P<photo>https://i\.vuzopedia\.ru/[^"]+)".*?'
    r'alt="(?P<alt>[^"]*)".*?class="vxVuzPrime__meta">(?P<meta>.*?)</div>.*?'
    r'href="/vuz/(?P<id>\d+)" class="vxVuzPrime__titleLink">\s*'
    r'<h2 class="vxVuzPrime__title">(?P<full>.*?)</h2>', re.S)


def text(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def crawl(pages: int):
    out, seen, empty = [], set(), 0
    for p in range(1, pages + 1):
        try:
            t = fetch(f'https://vuzopedia.ru/vuz?page={p}', ua=UA_BROWSER).decode('utf-8', 'replace')
        except Exception as e:
            print(f'страница {p}: не открылась — {e}', flush=True)
            continue
        t = re.sub(r'<style.*?</style>|<script.*?</script>', '', t, flags=re.S)
        n = 0
        for m in CARD.finditer(t):
            if m['id'] in seen:
                continue
            seen.add(m['id'])
            parts = [text(x) for x in re.findall(r'<span>(.*?)</span>', m['meta'])]
            # Шапка карточки: «Вуз», краткое название, город, «актуально: год».
            out.append({'id': m['id'], 'short': text(m['alt']), 'full': text(m['full']),
                        'city': parts[2] if len(parts) > 2 else '', 'photo': m['photo']})
            n += 1
        empty = empty + 1 if n == 0 else 0
        if p % 10 == 0:
            print(f'страница {p}: всего {len(out)}', flush=True)
        if empty >= 3:
            break
        time.sleep(1.5)
    CARDS.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print('карточек Vuzopedia:', len(out))

# ---------------------------------------------------------------- правило

LEGAL = {'ФГБОУ', 'ФГАОУ', 'ФГКОУ', 'ФГБВОУ', 'ФГОУ', 'ГБОУ', 'ГАОУ', 'ГКОУ', 'ГОУ', 'МБОУ',
         'АНО', 'АНОО', 'АНООВО', 'АОНО', 'АНОВО', 'ОАНО', 'ЧОУ', 'НОЧУ', 'ОЧУ', 'ЧУ', 'НОУ', 'ОУ',
         'ЧОУВО', 'ОЧУВО', 'ГАОУВО', 'ГБОУВО', 'ФГБОУВО', 'ООВО', 'ВО', 'ВПО', 'ДПО', 'УВО', 'ОУП',
         'ФГБУ', 'ФГБНУ', 'ФГБУН', 'ФБУН', 'ФГАУ', 'ФКУЗ', 'ГБУЗ', 'ГАУ', 'АО', 'БУ', 'НИЦ', 'РО',
         'ДОО', 'ДООВО', 'СО', 'УРО', 'ДВО', 'РАН', 'РФ', 'РАО', 'МЧС', 'ГПС', 'МВД', 'МИД',
         'ФСИН', 'ВНИИ', 'НИИ', 'ФИЦ', 'ФНЦ', 'НМИЦ', 'НИУ', 'ИМ', 'РОССИИ', 'МИНЗДРАВА',
         'СПБ', 'МСК', 'НН', 'ЕКБ', 'НСК',            # сокращения городов
         'ДЗМ', 'ДЗ', 'ФМБА', 'РЖД'}                  # пометки ведомств


def acronyms(*names):
    out = set()
    for s in names:
        for w in re.split(r'[^А-ЯЁA-Za-zа-яё]+', s):
            if len(re.findall(r'[А-ЯЁA-Z]', w)) >= 2 and len(w) >= 3:
                up = w.upper().replace('Ё', 'Е')
                if up not in LEGAL:
                    out.add(up)
    return out


NOISE = re.compile(
    r'федеральн\w*|государствен\w*\s+(?:бюджетн|автономн|казенн|казённ)\w*|бюджетн\w*|'
    r'автономн\w*|казённ\w*|казенн\w*|образовательн\w*\s+(?:учрежден|организац)\w*|'
    r'учрежден\w*|организац\w*|высш\w+\s+образован\w*|профессиональн\w*\s+образован\w*|'
    r'некоммерческ\w*|частн\w*|негосударствен\w*', re.I)


def fullname(s):
    q = re.findall(r'«([^»]+)»', s)
    core = (q[0] if q else s).lower().replace('ё', 'е')
    core = NOISE.sub(' ', core)
    core = re.sub(r'\bим\.?\s', 'имени ', core)
    return re.sub(r'[^а-яa-z0-9]+', ' ', core).strip()


def build_index(cards):
    by_acr, by_full = {}, {}
    for c in cards:
        k = city_key(c['city'])
        for a in acronyms(c['short']):
            by_acr.setdefault((k, a), set()).add(c['id'])
        for nm in (c['full'], c['short']):
            if fullname(nm):
                by_full.setdefault((k, fullname(nm)), set()).add(c['id'])
    return by_acr, by_full


def rule(org, by_acr, by_full):
    """(id карточки | None, объяснение)."""
    k = city_key(org['city'])
    for nm in (org['full'], org['short']):
        ids = by_full.get((k, fullname(nm)), set())
        if fullname(nm) and len(ids) == 1:
            return next(iter(ids)), 'город + полное название'
    found = {}
    for a in acronyms(org['short'], *org['acr']):
        ids = by_acr.get((k, a), set())
        if len(ids) > 1:
            return None, f'аббревиатура {a} в городе неоднозначна'
        if ids:
            found[next(iter(ids))] = f'город + аббревиатура {a}'
    if len(found) == 1:
        cid, why = next(iter(found.items()))
        return cid, why
    return None, 'аббревиатуры указывают на разные карточки' if found else 'нет совпадения'

# ---------------------------------------------------------------- подбор


def match():
    cards = {c['id']: c for c in json.loads(CARDS.read_text(encoding='utf-8'))}
    manifest = load_manifest()
    rejected = json.loads(REJECTED.read_text(encoding='utf-8')) if REJECTED.exists() else {}
    stub = bytes.fromhex(STUB.read_text().strip())
    by_acr, by_full = build_index(cards.values())

    need = head_without_photo(load_orgs(), manifest)
    hits, used = [], {}
    for o in need:
        cid, why = rule(o, by_acr, by_full)
        if cid:
            hits.append((o, cards[cid], why))
            used[cid] = used.get(cid, 0) + 1
    hits = [h for h in hits if used[h[1]['id']] == 1]

    if REVIEW.exists():
        shutil.rmtree(REVIEW)
    (REVIEW / 'img').mkdir(parents=True)
    out, stats = [], {}
    for o, c, why in hits:
        verdict = 'кандидат'
        # Отказ привязан к адресу снимка: если Vuzopedia сменит картинку,
        # пара снова попадёт на просмотр.
        if rejected.get(o['slug']) == c['photo']:
            verdict = 'отклонён раньше'
        elif c['short'].lower().startswith('логотип'):
            verdict = 'логотип: у карточки нет фото'
        else:
            dst = REVIEW / 'img' / f"{o['slug']}.src"
            try:
                dst.write_bytes(fetch(c['photo'], ua=UA_BROWSER, referer='https://vuzopedia.ru/'))
            except Exception as e:
                verdict = f'не скачалось: {e}'
            else:
                wh = subprocess.run(['identify', '-format', '%w %h', f'{dst}[0]'],
                                    capture_output=True, text=True).stdout.split()
                if len(wh) != 2 or int(wh[0]) < 300:
                    verdict = 'логотип: у карточки нет фото'
                elif sig_distance(stub, signature(dst)) < STUB_LIMIT:
                    verdict = 'заглушка Vuzopedia'
            time.sleep(0.5)
        stats[verdict.split(':')[0]] = stats.get(verdict.split(':')[0], 0) + 1
        out.append({'slug': o['slug'], 'ourShort': o['short'], 'city': o['city'],
                    'vpId': c['id'], 'vpShort': c['short'], 'vpFull': c['full'],
                    'photo': c['photo'], 'why': why, 'verdict': verdict})

    good = [x for x in out if x['verdict'] == 'кандидат']
    for i, x in enumerate(good):
        x['n'] = i
    CANDIDATES.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    if good:
        tiles = []
        for x in good:
            t = REVIEW / 'img' / f"{x['slug']}.tile.jpg"
            subprocess.run(['convert', str(REVIEW / 'img' / f"{x['slug']}.src") + '[0]', '-gravity', 'center',
                            '-crop', '520x390+0+0', '+repage', '-resize', '240x180', '-background', '#fff',
                            '-gravity', 'south', '-splice', '0x16', '-pointsize', '13',
                            '-annotate', '+0+2', str(x['n']), str(t)], capture_output=True)
            tiles.append(str(t))
        subprocess.run(['montage', *tiles, '-tile', '6x', '-geometry', '+3+3',
                        '-background', '#ccc', str(REVIEW / 'sheet.jpg')], capture_output=True)
    print('головных вузов без фото:', len(need), '| пар по правилу:', len(out))
    for k, v in sorted(stats.items(), key=lambda kv: -kv[1]):
        print(f'   {v:4}  {k}')
    if good:
        print(f'\nпросмотрите {REVIEW / "sheet.jpg"} — номера на плитках;')
        print('install --reject 3,7 отбросит кадры, которые не фотографии')

# ---------------------------------------------------------------- установка


def install(reject: set[int], reasons: dict[int, str]):
    out = json.loads(CANDIDATES.read_text(encoding='utf-8'))
    manifest = load_manifest()
    rejected = json.loads(REJECTED.read_text(encoding='utf-8')) if REJECTED.exists() else {}
    done = 0
    for x in out:
        if x['verdict'] != 'кандидат' or x['slug'] in manifest:
            continue
        if x['n'] in reject:
            rejected[x['slug']] = x['photo']
            continue
        w, h = convert(REVIEW / 'img' / f"{x['slug']}.src", x['slug'], crop_4x3=True)
        manifest[x['slug']] = {
            'src': 'vuzopedia', 'file': f"/photos/{x['slug']}.webp",
            'file360': f"/photos/{x['slug']}-360.webp", 'width': w, 'height': h,
            'caption': '', 'author': '', 'licence': '', 'licenceUrl': '',
            'source': f"https://vuzopedia.ru/vuz/{x['vpId']}", 'wikidata': ''}
        done += 1
    save_manifest(manifest)
    REJECTED.write_text(json.dumps(rejected, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'поставлено: {done} | отклонено при просмотре: {len(reject)} | в карте всего: {len(manifest)}')
    print('дальше: python3 scripts/photos/make_thumbs.py')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('crawl')
    c.add_argument('--pages', type=int, default=140)
    sub.add_parser('match')
    i = sub.add_parser('install')
    i.add_argument('--reject', default='', help='номера плиток через запятую')
    a = ap.parse_args()
    if a.cmd == 'crawl':
        crawl(a.pages)
    elif a.cmd == 'match':
        match()
    else:
        rej = {int(n) for n in a.reject.split(',') if n.strip()}
        install(rej, {})


if __name__ == '__main__':
    main()
