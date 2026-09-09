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
import hashlib
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
MAX_BOX_WIDTH = 420      # шире — слиплись соседние плитки
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


def find_highlighted(band: np.ndarray) -> list[tuple[int, int]]:
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

    runs = [(a, b) for a, b in runs if MIN_BOX_WIDTH <= b - a <= MAX_BOX_WIDTH]
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


def read_name(band: np.ndarray, box: tuple[int, int], cache: dict, lang: str) -> str:
    """Подпись в нижней части плитки. Одинаковые подписи читаются один раз."""
    x0, x1 = box
    rows = np.nonzero(((band[:, x0:x1 + 1, 1].astype(np.int16)
                        - band[:, x0:x1 + 1, 0].astype(np.int16)) > 50).any(axis=1))[0]
    if len(rows) == 0:
        return ""
    top, bottom = int(rows.min()), int(rows.max())
    crop = band[max(top, bottom - 30):bottom, x0 + 4:x1 - 3]
    if crop.size == 0:
        return ""
    key = hashlib.md5(crop.tobytes()).hexdigest()
    if key in cache:
        return cache[key]
    name = ""
    if shutil.which("tesseract"):
        from PIL import Image
        img = Image.fromarray(crop).resize((crop.shape[1] * 3, crop.shape[0] * 3))
        p = subprocess.run(["tesseract", "stdin", "stdout", "-l", lang, "--psm", "7"],
                           input=_png_bytes(img), capture_output=True)
        name = re.sub(r"[^\w .А-Яа-яЁё-]", "", p.stdout.decode("utf-8", "ignore")).strip()
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


def normalize(names: list[str]) -> dict:
    """Сводит варианты OCR одного имени к самому частому написанию."""
    from difflib import SequenceMatcher
    counts: dict[str, int] = {}
    for n in names:
        counts[n] = counts.get(n, 0) + 1
    canon: dict[str, str] = {}
    for name in sorted(counts, key=lambda n: -counts[n]):
        key = fold(name)
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
            marks.append((t, names))
        if i % 600 == 0:
            log(f"  разобрано {t / 60:.0f} мин, отметок {len(marks)}, "
                f"прошло {(time.time() - t0) / 60:.1f} мин")
    proc.wait()

    canon = normalize([n for _, ns in marks for n in ns])
    marks = [(t, sorted({canon.get(n, n) for n in ns})) for t, ns in marks]

    # мусор OCR: обрывки в один-два символа и подписи, мелькнувшие пару раз
    seen: dict[str, int] = {}
    for _, ns in marks:
        for n in ns:
            seen[n] = seen.get(n, 0) + 1
    junk = {n for n, c in seen.items() if len(n) < 3 or c < 5}
    if junk:
        log(f"отброшено как мусор OCR: {len(junk)} вариантов подписи")
    marks = [(t, [n for n in ns if n not in junk]) for t, ns in marks]
    marks = [(t, ns) for t, ns in marks if ns]

    # секунды с одним активным именем сшиваются в интервалы
    step = 1.0 / args.fps
    spans: list[dict] = []
    for t, names in marks:
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
