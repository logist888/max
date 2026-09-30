#!/usr/bin/env python3
"""Кто говорит — по картинке созвона, а не по голосу.

Клиенты видеовстреч (Yandex Telemost, Google Meet, Zoom) подсвечивают плитку
говорящего рамкой. Это независимый от звука и точный источник: рамка привязана к
имени участника, а не к тембру. Скрипт снимает кадры раз в секунду, находит
подсвеченные плитки, читает подпись с именем (tesseract, если установлен) и
отдаёт интервалы «имя говорит» в JSON.

Кадры, где подсвечены сразу несколько плиток, помечаются спорными: такие места
разбирает диаризация по голосу.

Запуск: python3 scripts/transcribe/video_speaker_tags.py запись.webm -o tags.json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

BAND_HEIGHT = 220        # верхняя полоса с плитками участников, px
MIN_BOX_WIDTH = 60       # уже — не плитка, а блик
MAX_BOX_SHARE = 0.6      # шире доли кадра — это рамка демонстрации, а не плитка
MIN_GREEN_PIXELS = 300


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def video_size(path: Path) -> tuple[int, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(path)],
        capture_output=True, text=True, check=True).stdout.strip().splitlines()[0]
    w, h = out.split("x")
    return int(w), int(h)


def green_mask(band: np.ndarray) -> np.ndarray:
    r = band[:, :, 0].astype(np.int16)
    g = band[:, :, 1].astype(np.int16)
    b = band[:, :, 2].astype(np.int16)
    return (g > 120) & (g - r > 50) & (g - b > 50)


def find_highlighted(band: np.ndarray, max_width: int | None = None) -> list[tuple[int, int]]:
    """Границы подсвеченных плиток по x.

    Опора — горизонтальные грани рамки: сплошной отрезок ровно по ширине плитки.
    Группировать просто все зелёные пиксели нельзя: соседние подсвеченные плитки
    разделены зазором в несколько пикселей и слипаются в одну коробку, после чего
    OCR читает две подписи как одно имя.
    """
    mask = green_mask(band)
    if mask.sum() < MIN_GREEN_PIXELS:
        return []
    per_row = mask.sum(axis=1)
    strong = np.nonzero(per_row >= MIN_BOX_WIDTH)[0]      # строки с гранями
    runs: list[tuple[int, int]] = []
    for y in strong:
        cols = np.nonzero(mask[y])[0]
        start = prev = cols[0]
        for x in cols[1:]:
            if x - prev > 6:                              # зазор между плитками
                runs.append((start, prev))
                start = x
            prev = x
        runs.append((start, prev))

    limit = max_width or int(band.shape[1] * MAX_BOX_SHARE)
    runs = [(a, b) for a, b in runs if MIN_BOX_WIDTH <= b - a <= limit]
    if not runs:
        return []
    runs.sort()
    boxes = [list(runs[0])]
    for a, b in runs[1:]:
        if a <= boxes[-1][1] - 20:                        # тот же прямоугольник
            boxes[-1][1] = max(boxes[-1][1], b)
        else:
            boxes.append([a, b])
    return [(a, b) for a, b in boxes]


def trim_to_text(crop: np.ndarray) -> np.ndarray:
    """Обрезать кроп по столбцам, где есть светлый текст.

    Подпись — короткая плашка по центру плитки, а кроп идёт во всю её ширину.
    В сетке на весь экран это почти тысяча пикселей пустоты, и tesseract тратит
    на неё секунды. Режем по крайним столбцам с белым.
    """
    cols = np.nonzero((crop.min(axis=2) > 150).any(axis=0))[0]
    if len(cols) == 0:
        return crop
    a, b = int(cols.min()), int(cols.max())
    return crop[:, max(0, a - 6):b + 7]


def stable_key(crop: np.ndarray, box: tuple[int, int]) -> str:
    """Ключ кеша, не чувствительный к шуму кодека.

    Точный хеш пикселей здесь бесполезен: подпись дрожит от кадра к кадру, и
    кеш промахивается почти всегда — OCR идёт на каждом кадре. Вместо этого
    огрубляем кроп до сетки 32×4 и сравниваем по яркости блоков; перестановка
    плиток меняет рисунок подписи, поэтому такой ключ её тоже ловит.
    """
    g = crop.mean(axis=2)
    h, w = g.shape
    gh, gw = max(1, h // 4), max(1, w // 32)
    grid = g[:gh * 4, :gw * 32].reshape(4, gh, 32, gw).mean(axis=(1, 3))
    bits = (grid > np.median(grid)).astype(np.uint8).flatten()
    return f"{box[0] // 8}:{box[1] // 8}:" + "".join(map(str, bits))


def box_bounds(band: np.ndarray, box: tuple[int, int]) -> tuple[int, int] | None:
    """Верх и низ подсвеченной плитки по зелёным строкам рамки."""
    x0, x1 = box
    rows = np.nonzero(((band[:, x0:x1 + 1, 1].astype(np.int16)
                        - band[:, x0:x1 + 1, 0].astype(np.int16)) > 50).any(axis=1))[0]
    if len(rows) == 0:
        return None
    return int(rows.min()), int(rows.max())


def avatar_print(band: np.ndarray, box: tuple[int, int]) -> np.ndarray | None:
    """Отпечаток картинки участника внутри плитки.

    Подпись — ненадёжный признак: при демонстрации экрана плитки сжимаются в
    узкую полосу, буквы мельчают и OCR выдаёт огрызки. Аватарка же не меняется
    всю встречу и не зависит ни от раскладки, ни от размера плитки, поэтому по
    ней плитки одного человека сшиваются между раскладками.
    """
    bounds = box_bounds(band, box)
    if bounds is None:
        return None
    top, bottom = bounds
    x0, x1 = box
    inner = band[top + 6:bottom - 6, x0 + 6:x1 - 5]
    if inner.shape[0] < 16 or inner.shape[1] < 16:
        return None
    side = min(inner.shape[:2])                       # аватарка вписана в центр
    y = (inner.shape[0] - side) // 2
    x = (inner.shape[1] - side) // 2
    sq = inner[y:y + side, x:x + side].mean(axis=2)
    k = side // 16
    if k < 1:
        return None
    grid = sq[:k * 16, :k * 16].reshape(16, k, 16, k).mean(axis=(1, 3))
    v = grid.flatten() - grid.mean()
    n = np.linalg.norm(v)
    return (v / n).astype(np.float32) if n > 1e-6 else None


def read_name(band: np.ndarray, box: tuple[int, int], cache: dict, lang: str) -> str:
    """Подпись в нижней части плитки. Одинаковые подписи читаются один раз."""
    x0, x1 = box
    bounds = box_bounds(band, box)
    if bounds is None:
        return ""
    top, bottom = bounds
    crop = band[max(top, bottom - 30):bottom, x0 + 4:x1 - 3]
    if crop.size == 0:
        return ""
    crop = trim_to_text(crop)
    key = stable_key(crop, box)
    if key in cache:
        return cache[key]
    name = ""
    if shutil.which("tesseract"):
        from PIL import Image
        scale = max(1, min(3, 96 // max(1, crop.shape[0])))
        img = Image.fromarray(crop).resize((crop.shape[1] * scale, crop.shape[0] * scale))
        p = subprocess.run(["tesseract", "stdin", "stdout", "-l", lang, "--psm", "7"],
                           input=_png_bytes(img), capture_output=True)
        name = re.sub(r"[^\w .А-Яа-яЁё-]", "", p.stdout.decode("utf-8", "ignore")).strip()
        # подпись лежит поверх кадра, и по краям кропа налипают куски картинки:
        # оставляем то, что похоже на имя — слова от заглавной буквы
        m = re.search(r"[A-ZА-ЯЁ][\w.-]*(?:\s+[A-ZА-ЯЁa-zа-яё][\w.-]*)*", name)
        name = m.group(0).strip() if m else ""
        name = re.sub(r"(?:\s+\S{1,2})+$", "", name).strip()   # хвост из огрызков
        name = re.sub(r"^(?:\S{1,2}\s+)+", "", name).strip()   # и такие же огрызки в начале
    cache[key] = name
    return name


def _png_bytes(img) -> bytes:
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# латинские буквы, неотличимые на вид от кириллических: OCR путает их в именах
LOOKALIKE = str.maketrans("aAeEoOpPcCxXyYkKmMhHtTbBnN", "аАеЕоОрРсСхХуУкКмМнНтТвВпН")


def fold(name: str) -> str:
    return re.sub(r"\W", "", name.translate(LOOKALIKE).lower())


def assign_clusters(prints: list[list], threshold: float = 0.88) -> list[list]:
    """Разложить отпечатки плиток по участникам.

    Жадно: отпечаток идёт к первому центру, с которым сходится выше порога,
    иначе заводит свой. Аватарка статична, поэтому кластеров выходит немного —
    по числу участников плюс редкий мусор от чужих рамок, который остаётся
    безымянным и отсеивается.
    """
    centers: list[np.ndarray] = []
    out: list[list] = []
    for row in prints:
        ids = []
        for p in row:
            if p is None:
                ids.append(None)
                continue
            best, score = None, threshold
            for k, c in enumerate(centers):
                s = float(np.dot(p, c))
                if s > score:
                    best, score = k, s
            if best is None:
                centers.append(p)
                best = len(centers) - 1
            ids.append(best)
        out.append(ids)
    return out


def normalize(names: list[str], known: list[str] | None = None) -> dict:
    """Сводит варианты OCR одного имени к самому частому написанию.

    Если состав участников известен, чтения притягиваются к нему: это отсекает
    заголовки со слайдов, которые при демонстрации экрана попадают в разбор
    наравне с подписями плиток — зелёные линии вёрстки неотличимы от подсветки.
    """
    from difflib import SequenceMatcher
    counts: dict[str, int] = {}
    for n in names:
        counts[n] = counts.get(n, 0) + 1
    canon: dict[str, str] = {}
    for name in sorted(counts, key=lambda n: -counts[n]):
        key = fold(name)
        if known:
            hit = max(known, key=lambda k: SequenceMatcher(None, key, fold(k)).ratio())
            ratio = SequenceMatcher(None, key, fold(hit)).ratio()
            # огрызок подписи короче имени — сверяем его как часть, а не целиком
            part = max((SequenceMatcher(None, key, fold(k)[:len(key)]).ratio()
                        for k in known), default=0.0) if len(key) >= 4 else 0.0
            canon[name] = hit if (ratio > 0.62 or part > 0.85) else ""
            continue
        match = next((c for c in dict.fromkeys(canon.values())
                      if SequenceMatcher(None, key, fold(c)).ratio() > 0.8), name)
        canon[name] = match
    return canon


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Разметка активного говорящего по подсветке плиток в записи созвона")
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True, help="JSON с интервалами")
    ap.add_argument("--fps", type=float, default=1.0, help="кадров в секунду на разбор")
    ap.add_argument("--band", type=int, default=BAND_HEIGHT, help="высота полосы плиток, px")
    ap.add_argument("--lang", default="rus+eng", help="языки tesseract")
    ap.add_argument("--participants", default="",
                    help="известный состав через запятую: чтения сводятся к нему, "
                         "остальное отбрасывается (спасает от заголовков со слайдов)")
    args = ap.parse_args()

    if shutil.which("ffmpeg") is None:
        sys.exit("нет ffmpeg")
    if not shutil.which("tesseract"):
        log("tesseract не найден — имена читаться не будут, останутся номера плиток")

    w, h = video_size(args.input)
    band_h = min(args.band, h)
    log(f"видео {w}×{h}, полоса плиток {band_h}px, {args.fps} кадр/с")

    proc = subprocess.Popen(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", str(args.input),
         "-vf", f"fps={args.fps},crop={w}:{band_h}:0:0",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE, bufsize=10 ** 8)

    frame_bytes = w * band_h * 3
    cache: dict[str, str] = {}
    marks: list[tuple[float, list[str]]] = []
    prints: list[list[np.ndarray | None]] = []
    i, t0 = 0, time.time()
    while True:
        buf = proc.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        t = i / args.fps
        i += 1
        band = np.frombuffer(buf, dtype=np.uint8).reshape(band_h, w, 3)
        boxes = find_highlighted(band)
        if boxes:
            names = [read_name(band, b, cache, args.lang) or f"плитка@{b[0]}" for b in boxes]
            prints.append([avatar_print(band, b) for b in boxes])
            marks.append((t, names, [b[0] for b in boxes]))
        if i % 600 == 0:
            log(f"  разобрано {t / 60:.0f} мин, отметок {len(marks)}, "
                f"прошло {(time.time() - t0) / 60:.1f} мин")
    proc.wait()

    known = [p.strip() for p in args.participants.split(",") if p.strip()] \
        if args.participants else None
    canon = normalize([n for _, ns, _ in marks for n in ns], known)
    marks = [(t, [canon.get(n, n) for n in ns], xs) for t, ns, xs in marks]

    counts: dict[str, int] = {}
    for _, ns, _ in marks:
        for n in ns:
            counts[n] = counts.get(n, 0) + 1
    if known:
        solid = {n for n in counts if n in known}
    else:
        # огрызок OCR вроде «eee» или «Mruk» тоже попадается часто, поэтому от имени
        # требуется ещё и правдоподобная длина: короче пяти букв — только с фамилией
        solid = {n for n, c in counts.items()
                 if c >= 10 and not n.startswith("плитка@")
                 and (len(n) >= 5 or (len(n) >= 4 and " " in n))}

    # аватарка — самый устойчивый признак: сшиваем по ней плитки одного человека,
    # как бы ни менялись раскладка и качество подписи
    cluster_of = assign_clusters(prints)
    by_cluster: dict[int, dict[str, int]] = {}
    for (_, ns, _), cl in zip(marks, cluster_of):
        for n, c in zip(ns, cl):
            if c is not None and n in solid:
                by_cluster.setdefault(c, {})
                by_cluster[c][n] = by_cluster[c].get(n, 0) + 1
    cluster_name = {c: max(v, key=v.get) for c, v in by_cluster.items()}
    if cluster_name:
        log(f"плиток по аватарке: {len(cluster_name)} "
            f"({', '.join(sorted(set(cluster_name.values())))})")

    # позиция плитки — запасной признак: в неизменной раскладке она тоже надёжна
    by_slot: dict[int, dict[str, int]] = {}
    for _, ns, xs in marks:
        for n, x in zip(ns, xs):
            if n in solid:
                by_slot.setdefault(x // 40, {})
                by_slot[x // 40][n] = by_slot[x // 40].get(n, 0) + 1
    slot_name = {s: max(c, key=c.get) for s, c in by_slot.items()}

    by_read = by_avatar = by_pos = dropped = 0
    for i, (tm, ns, xs) in enumerate(marks):
        fixed = []
        for n, x, c in zip(ns, xs, cluster_of[i]):
            if n in solid:
                fixed.append(n)
                by_read += 1
            elif c is not None and c in cluster_name:
                fixed.append(cluster_name[c])         # подпись не далась — узнаём по аватарке
                by_avatar += 1
            elif x // 40 in slot_name:
                fixed.append(slot_name[x // 40])
                by_pos += 1
            else:
                dropped += 1                          # чужая рамка, не плитка участника
        marks[i] = (tm, fixed, xs)
    log(f"имя по подписи {by_read}, по аватарке {by_avatar}, "
        f"по позиции {by_pos}, отброшено {dropped}")
    marks = [(t, sorted(set(ns)), xs) for t, ns, xs in marks if ns]

    # секунды с одним активным именем сшиваются в интервалы
    step = 1.0 / args.fps
    spans: list[dict] = []
    for t, names, _ in marks:
        disputed = len(names) > 1
        name = names[0] if not disputed else "|".join(names)
        if spans and spans[-1]["name"] == name and t - spans[-1]["end"] <= step * 1.5:
            spans[-1]["end"] = t + step
        else:
            spans.append({"start": t, "end": t + step, "name": name, "disputed": disputed})

    speakers: dict[str, float] = {}
    for s in spans:
        if not s["disputed"]:
            speakers[s["name"]] = speakers.get(s["name"], 0.0) + s["end"] - s["start"]

    args.out.write_text(json.dumps(
        {"source": args.input.name, "fps": args.fps, "spans": spans,
         "speakers": {k: round(v, 1) for k, v in sorted(speakers.items(), key=lambda x: -x[1])}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"готово: {len(spans)} интервалов, {(time.time() - t0) / 60:.1f} мин")
    for name, sec in sorted(speakers.items(), key=lambda x: -x[1]):
        log(f"  {name}: {sec / 60:.1f} мин")


if __name__ == "__main__":
    main()
