# -*- coding: utf-8 -*-
"""Разбор PDF «Глобальная онтология образовательного выбора» v2.0 в JSON: дерево вопросов и сценарии главы 9.
Запуск: python scripts/ontology_cjm/parse_ontology.py <онтология.pdf> <папка-результата>
Нужен pdftotext (poppler-utils)."""
import json
import os
import re
import subprocess
import sys

NOISE = re.compile(r"^(MainExperts /|Версия 2\.0|26 ноября 2026|\d+)\s*$|^MainExperts / Глобальная")
COUNTRIES = "Россия|Великобритания|США|Канада|Швейцария|Франция|Италия|ОАЭ|Испания|Сингапур|Гонконг|Материковый Китай|Германия|Австралия"


def pdftext(pdf, first, last, layout):
    cmd = ["pdftotext"] + (["-layout"] if layout else []) + ["-f", str(first), "-l", str(last), pdf, "-"]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def parse_tree(pdf):
    """Глава 5, страницы 26–52. Лист: код, действие, результат; группа: заголовок, листья."""
    items = []
    cur = None
    for ln in pdftext(pdf, 26, 52, True).split("\n"):
        s = ln.rstrip()
        if not s.strip() or NOISE.match(s.strip()):
            continue
        m = re.match(r"^(Q\d\d) · (.+)$", s.strip())
        if m:
            items.append(("branch", m.group(1), m.group(2)))
            cur = None
            continue
        m = re.match(r"^\s*(Q\d\d\.\d\d[a-z]?)\s{2,}(.+?)(\s{2,}(.+))?$", s)
        if m:
            cur = [m.group(1), m.group(2).strip(), (m.group(4) or "").strip()]
            items.append(("leaf", cur))
            continue
        if re.match(r"^\s*Код\b", s):
            continue
        if cur and s.startswith(" "):
            parts = re.split(r"\s{2,}", s.strip())
            if len(parts) == 1:
                if len(s) - len(s.lstrip()) < 30:
                    cur[1] += " " + parts[0]
                else:
                    cur[2] += " " + parts[0]
            else:
                cur[1] += " " + parts[0]
                cur[2] += " " + " ".join(parts[1:])
            continue
        items.append(("head", s.strip()))
        cur = None
    branches, pending = [], None
    for it in items:
        if it[0] == "branch":
            branches.append({"code": it[1], "name": it[2], "groups": []})
            pending = None
        elif it[0] == "head" and branches:
            pending = it[1]          # заголовком группы считается последняя строка перед листьями
        elif it[0] == "leaf" and branches:
            if pending is not None:
                branches[-1]["groups"].append({"name": pending, "leaves": []})
                pending = None
            code, action, result = it[1]
            branches[-1]["groups"][-1]["leaves"].append({"code": code, "action": action, "result": result})
    return branches


def clean(t):
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"26 ноября 2026 \d+ MainExperts / Глобальная онтология образовательного выбора( •)? Версия 2\.0", lambda m: " •" if m.group(1) else " ", t)
    t = re.sub(r" 26 ноября 2026 \d+$", "", t)
    return re.sub(r"\s+", " ", t).strip()


def parse_scenarios(pdf):
    """Глава 9, страницы 69–72: страновые сценарии (Запрос, Ожидаемая модель, Ловушка, Основание)."""
    txt = clean(pdftext(pdf, 69, 72, False).replace("•\n", "• "))
    body = clean(txt.split("Глобальные отрицательные проверки")[0].split("9. Проверочные сценарии", 1)[1])
    parts = re.split(r"(?<=[.»]) (?=(?:%s) · )" % COUNTRIES, body)
    pat = re.compile(r"^(?:.*?реестра источников\. )?(%s) · (.+?) • Запрос\. (.+?) • Ожидаемая модель\. (.+?) • Ловушка\. (.+?) • Основание\. (.+?)$" % COUNTRIES)
    out = []
    for p in parts:
        m = pat.match(p.strip())
        if m:
            out.append(dict(zip(("country", "topic", "query", "model", "trap", "basis"), m.groups())))
    return out


def main():
    pdf, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    tree, sc = parse_tree(pdf), parse_scenarios(pdf)
    for name, data in (("qtree.json", tree), ("scenarios.json", sc)):
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
    n = sum(len(g["leaves"]) for b in tree for g in b["groups"])
    print("ветвей %d, групп %d, листьев %d, сценариев %d" % (len(tree), sum(len(b["groups"]) for b in tree), n, len(sc)))


if __name__ == "__main__":
    main()
