# -*- coding: utf-8 -*-
"""Командная строка: python scripts/cjm_map/build.py journey.yaml --out out/ [--png] [--pdf] [--html] [--check]"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from cjm_map import export, model, render  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description="Карта CJM в SVG по journey.yaml")
    ap.add_argument("journey", help="файл данных пути (YAML)")
    ap.add_argument("--out", default="out", help="папка результата (по умолчанию out/)")
    ap.add_argument("--check", action="store_true", help="только проверить данные, ничего не строить")
    ap.add_argument("--png", action="store_true", help="дополнительно PNG (нужен Playwright)")
    ap.add_argument("--pdf", action="store_true", help="дополнительно PDF (нужен Playwright)")
    ap.add_argument("--html", action="store_true", help="дополнительно map.html с масштабированием")
    a = ap.parse_args(argv)
    try:
        doc = model.load(a.journey)
    except model.ValidationError as e:
        print("Данные не прошли проверку (%d):" % len(e.problems), file=sys.stderr)
        for p in e.problems:
            print("  " + p, file=sys.stderr)
        return 2
    for w in doc["_warnings"]:
        print("Предупреждение: " + w, file=sys.stderr)
    stats = "дорожек %d, этапов %d, шагов %d, связей %d, стикеров %d, связей стикеров %d, экранов %d, колонок %d" % (
        len(doc["lanes"]), len(doc["stages"]), len(doc["flow"]["nodes"]), len(doc["flow"].get("edges", [])),
        len(doc.get("stickies", [])), len(doc.get("sticky_links", [])), len(doc.get("screens", [])), doc["_ncols"])
    if a.check:
        print("Проверка пройдена: " + stats)
        return 0
    os.makedirs(a.out, exist_ok=True)
    svg = render.build_svg(doc, "outline")
    txt = render.build_svg(doc, "text")
    p1, p2 = os.path.join(a.out, "map.svg"), os.path.join(a.out, "map-text.svg")
    with open(p1, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg)
    with open(p2, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    made = ["map.svg (%d КБ, буквы контурами)" % (len(svg) // 1024), "map-text.svg (%d КБ, текст выделяется)" % (len(txt) // 1024)]
    if a.html:
        export.write_html(p2, os.path.join(a.out, "map.html"), doc["meta"]["title"])
        made.append("map.html")
    if a.png or a.pdf:
        r = export.write_png_pdf(p1, a.out, a.png, a.pdf)
        made += r
    print("Собрано: " + stats)
    for m in made:
        print("  " + os.path.join(a.out, m))
    return 0


if __name__ == "__main__":
    sys.exit(main())
