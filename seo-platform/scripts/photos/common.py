"""Общее для скриптов фотографий вузов: пути, карта соответствий, вузы,
работа с изображениями.

Карта соответствий — data/photos/vuz-photos.json, slug → запись:
  src        commons | vuzopedia (нет поля — commons)
  file       /photos/<slug>.webp        широкий, до 800 px (Vuzopedia — 520)
  file360    /photos/<slug>-360.webp    для телефонов
  thumb      /photos/<slug>-thumb.webp  превью для списков, 192×144
  width, height
  caption, author, licence, licenceUrl  — только у Викисклада
  source     страница файла на Викискладе или карточка на Vuzopedia
  wikidata   Q-идентификатор (у Викисклада)
"""
import json, pathlib, re, subprocess, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]            # seo-platform/
APP = ROOT / 'app'
PHOTOS = APP / 'public' / 'photos'
DATA = ROOT / 'data' / 'photos'
MANIFEST = DATA / 'vuz-photos.json'
ORGS = APP / 'build' / 'org-cards.json'

# Викимедиа просит представляться и давать контакт. Адрес проекта сюда
# вписать, когда он появится: запросы с контактом ограничивают мягче.
UA_BOT = 'vuz-navigator-image-import/1.0 (https://vuz-navigator.ru)'
UA_BROWSER = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/131.0 Safari/537.36')


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {}


def save_manifest(m: dict) -> None:
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')


def load_orgs() -> list:
    """Вузы из сборки. Перед запуском скриптов нужна свежая сборка данных."""
    if not ORGS.exists():
        raise SystemExit(f'нет {ORGS} — сначала соберите данные сайта')
    out = []
    for o in json.loads(ORGS.read_text(encoding='utf-8')):
        out.append({'slug': o['slug'], 'kind': o['kind'], 'short': o['shortName'],
                    'full': o['fullName'], 'city': o['cityName'],
                    'sites': o.get('websites') or [], 'acr': o.get('acronyms') or []})
    return out


def head_without_photo(orgs: list, manifest: dict) -> list:
    """Головные вузы без снимка. Филиалам здание головного вуза не принадлежит."""
    return [o for o in orgs if o['kind'] == 'головной' and o['slug'] not in manifest]


def fetch(url: str, ua: str = UA_BOT, tries: int = 5, referer: str | None = None,
          data: bytes | None = None, pause: float = 3.0) -> bytes:
    headers = {'User-Agent': ua}
    if referer:
        headers['Referer'] = referer
    last = None
    for a in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            return urllib.request.urlopen(req, timeout=90).read()
        except Exception as e:                      # сеть и 429 — повтор с паузой
            last = e
            wait = pause * (a + 1) * (5 if getattr(e, 'code', None) == 429 else 1)
            time.sleep(wait)
    raise RuntimeError(f'{url}: {last}')


def convert(src: pathlib.Path, slug: str, crop_4x3: bool) -> tuple[int, int]:
    """Делает <slug>.webp и <slug>-360.webp. crop_4x3 — кроп по центру до 4:3
    (для вертикальных снимков Vuzopedia), иначе — уменьшение до 800 px."""
    main, small = PHOTOS / f'{slug}.webp', PHOTOS / f'{slug}-360.webp'
    if crop_4x3:
        geo = ['-gravity', 'center', '-crop', '520x390+0+0', '+repage']
        steps = ((main, geo), (small, geo + ['-resize', '360x360>']))
    else:
        steps = ((main, ['-resize', '800x800>']), (small, ['-resize', '360x360>']))
    for dst, ops in steps:
        r = subprocess.run(['convert', f'{src}[0]', '-auto-orient', '-strip', *ops,
                            '-quality', '76', str(dst)], capture_output=True)
        if r.returncode != 0 or not dst.exists():
            raise RuntimeError(f'{slug}: не сконвертировалось — {r.stderr.decode()[:200]}')
    w, h = subprocess.run(['identify', '-format', '%w %h', str(main)],
                          capture_output=True, text=True).stdout.split()
    return int(w), int(h)


def signature(path) -> bytes:
    """Отпечаток картинки: центр 4:3, уменьшенный до 32×24, оттенки серого."""
    return subprocess.run(['convert', f'{path}[0]', '-gravity', 'center', '-crop', '520x390+0+0',
                           '+repage', '-resize', '32x24!', '-colorspace', 'Gray', '-depth', '8',
                           'gray:-'], capture_output=True).stdout


def sig_distance(a: bytes, b: bytes) -> float:
    n = min(len(a), len(b))
    return sum(abs(a[i] - b[i]) for i in range(n)) / n if n else 999.0


def domain(url: str) -> str:
    h = urllib.parse.urlsplit(url if '//' in url else 'http://' + url).netloc.lower().split(':')[0]
    return h[4:] if h.startswith('www.') else h


def city_key(c: str) -> str:
    """Город целиком. Сравнение по началу слова недопустимо: так однажды
    совпали Владивосток с Владимиром и Томск с Омском."""
    c = c.lower().replace('ё', 'е').strip()
    return re.sub(r'^(г\.?|город|о\.)\s*', '', c).strip()
