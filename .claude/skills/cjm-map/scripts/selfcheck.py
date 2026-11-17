# -*- coding: utf-8 -*-
"""Самопроверка скилла: python scripts/selfcheck.py
Собирает оба примера, проверяет состав SVG, повторяемость сборки и реакцию проверки данных на поломки."""
import hashlib
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "scripts", "cjm_map", "build.py")
OK, BAD = [], []


def run(args):
    return subprocess.run([sys.executable, BUILD] + args, capture_output=True, text=True)


def check(name, cond, detail=""):
    (OK if cond else BAD).append(name + ((": " + detail) if detail and not cond else ""))
    print(("  [ok]   " if cond else "  [FAIL] ") + name + ((" — " + detail) if detail and not cond else ""))


def sha(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


tmp = tempfile.mkdtemp(prefix="cjm_check_")
print("Сборка примеров во временную папку", tmp)
for name in ("minimal", "example"):
    r = run([os.path.join(ROOT, "examples", "journey.%s.yaml" % name), "--out", os.path.join(tmp, name)])
    check("сборка %s" % name, r.returncode == 0, r.stderr.strip()[:300])
    svg_p = os.path.join(tmp, name, "map.svg")
    if r.returncode:
        continue
    with open(svg_p, encoding="utf-8") as fh:
        svg = fh.read()
    bad = [t for t in ("<text", "<marker", "<filter", "<foreignObject", "<use") if t in svg]
    check("%s: в map.svg нет %s" % (name, ", ".join(("<text", "<marker", "<filter", "<foreignObject", "<use"))), not bad, ", ".join(bad))
    check("%s: нет вложенных <svg>" % name, len(re.findall(r"<svg\b", svg)) == 1)
    r2 = run([os.path.join(ROOT, "examples", "journey.%s.yaml" % name), "--out", os.path.join(tmp, name + "2")])
    check("%s: повторная сборка даёт тот же файл" % name, sha(svg_p) == sha(os.path.join(tmp, name + "2", "map.svg")))
    with open(os.path.join(tmp, name, "map-text.svg"), encoding="utf-8") as fh:
        check("%s: в map-text.svg есть <text>" % name, "<text" in fh.read())

src = open(os.path.join(ROOT, "examples", "journey.minimal.yaml"), encoding="utf-8").read()
cases = {"неизвестная дорожка": src.replace("lane: site, text: \"Подходит", "lane: kosmos, text: \"Подходит"),
         "битая связь": src.replace("{from: call, to: doc}", "{from: call, to: nowhere}"),
         "пустой текст": src.replace("text: \"Сомнение\"", "text: \"\"")}
for title, body in cases.items():
    p = os.path.join(tmp, "bad.yaml")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(body)
    r = run([p, "--out", os.path.join(tmp, "bad_out")])
    check("проверка данных ловит: %s" % title, r.returncode == 2 and "bad.yaml:" in r.stderr and not os.path.exists(os.path.join(tmp, "bad_out", "map.svg")), r.stderr.strip()[:200])

print("\nИтог: %d успешно, %d с ошибкой" % (len(OK), len(BAD)))
sys.exit(1 if BAD else 0)
