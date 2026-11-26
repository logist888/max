"""Превью фотографий вузов для списков: 192×144, кроп по центру до 4:3.

В списке превью показывается 96×72, файл вдвое крупнее — для экранов с
высокой плотностью. Отдельный файл, а не мобильная версия на 360 px: на
странице «Вузы» 1 785 карточек, и каждый лишний килобайт там умножается.

Скрипт идемпотентный: пропускает вузы, у которых превью уже есть, и
дописывает поле thumb в карту соответствий. Запускать после любого
пополнения карты фотографий.

    python3 scripts/photos/make_thumbs.py
"""
import json, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]          # seo-platform/
OUT = ROOT / 'app' / 'public' / 'photos'
MAN = ROOT / 'data' / 'photos' / 'vuz-photos.json'


def main():
    m = json.loads(MAN.read_text(encoding='utf-8'))
    made = 0
    for slug, v in m.items():
        dst = OUT / f'{slug}-thumb.webp'
        if not dst.exists():
            r = subprocess.run(['convert', str(OUT / f'{slug}.webp'), '-strip',
                                '-resize', '192x144^', '-gravity', 'center', '-extent', '192x144',
                                '-quality', '72', str(dst)], capture_output=True)
            if r.returncode != 0 or not dst.exists():
                print('не вышло:', slug, r.stderr.decode()[:200])
                continue
            made += 1
        v['thumb'] = f'/photos/{slug}-thumb.webp'
    MAN.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')
    size = sum((OUT / f'{s}-thumb.webp').stat().st_size for s in m if (OUT / f'{s}-thumb.webp').exists())
    print(f'превью сделано: {made} | всего с превью: {len(m)} | общий вес: {size // 1024} КБ')


if __name__ == '__main__':
    main()
