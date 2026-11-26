# -*- coding: utf-8 -*-
"""Шрифт Inter: метрики, перенос строк по ширине, контуры букв для SVG без <text>."""
import os
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

_HERE = os.path.dirname(os.path.abspath(__file__))
_FILES = {"400": "Inter-Regular.otf", "600": "Inter-SemiBold.otf", "700": "Inter-Bold.otf"}
_cache = {}
missing = set()   # символы, которых нет в шрифте: в контурном SVG они пропадут


def _font_dirs():
    dirs = []
    if os.environ.get("CJM_FONT_DIR"):
        dirs.append(os.environ["CJM_FONT_DIR"])
    dirs.append(os.path.join(_HERE, "..", "..", "fonts"))
    dirs.append("/usr/share/fonts/opentype/inter")
    return dirs


def _weight_key(weight):
    w = str(weight)
    if w in ("700", "bold", "800", "900"):
        return "700"
    if w in ("600", "500"):
        return "600"
    return "400"


def _load(weight):
    k = _weight_key(weight)
    if k not in _cache:
        for d in _font_dirs():
            p = os.path.join(d, _FILES[k])
            if os.path.exists(p):
                f = TTFont(p)
                _cache[k] = (f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm, f["hmtx"])
                break
        else:
            sys.exit("Не найден шрифт %s. Он лежит в .claude/skills/cjm-map/fonts/; "
                     "если папку убрали, задайте CJM_FONT_DIR (каталог с Inter-Regular/SemiBold/Bold.otf)." % _FILES[k])
    return _cache[k]


def width(text, size, weight=400):
    gs, cmap, upm, hmtx = _load(weight)
    total = 0
    for ch in text:
        n = cmap.get(ord(ch))
        if not n and not ch.isspace():
            missing.add(ch)
        total += hmtx[n][0] if n else upm * 0.3
    return total * size / upm


def wrap(text, size, weight, max_w):
    """Перенос по словам; слово длиннее строки режется по символам."""
    lines = []
    for para in str(text).split("\n"):
        cur = ""
        for word in para.split():
            cand = word if not cur else cur + " " + word
            if width(cand, size, weight) <= max_w:
                cur = cand
                continue
            if cur:
                lines.append(cur)
            cur = ""
            while width(word, size, weight) > max_w and len(word) > 1:
                k = len(word)
                while k > 1 and width(word[:k], size, weight) > max_w:
                    k -= 1
                lines.append(word[:k])
                word = word[k:]
            cur = word
        lines.append(cur)
    return lines or [""]


def _num(v):
    return ("%.1f" % v).rstrip("0").rstrip(".")


def outline(text, x, y, size, weight, fill, anchor="start", stroke=None, sw=0):
    """Контуры букв одним <path>; y — базовая линия."""
    gs, cmap, upm, hmtx = _load(weight)
    s = size / upm
    names = [cmap.get(ord(c)) for c in text]
    adv = [(hmtx[n][0] if n else upm * 0.3) for n in names]
    total = sum(adv) * s
    x0 = x if anchor == "start" else (x - total / 2 if anchor == "middle" else x - total)
    d = []
    cum = 0.0
    for n, a in zip(names, adv):
        if n and n != "space":
            pen = SVGPathPen(gs, ntos=_num)
            gs[n].draw(TransformPen(pen, (s, 0, 0, -s, x0 + cum * s, y)))
            p = pen.getCommands()
            if p:
                d.append(p)
        cum += a
    if not d:
        return ""
    dd = "".join(d)
    out = ""
    if stroke:
        out += '<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>' % (dd, stroke, stroke, sw)
    return out + '<path d="%s" fill="%s"/>' % (dd, fill)
