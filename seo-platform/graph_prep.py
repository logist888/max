#!/usr/bin/env python3
"""Тяжёлый разбор сырых источников графа → компактные промежуточные JSON.
Изолирует парсинг больших дампов (ESCO 656 МБ, ОКЗ 386 стр.) в Python; TS-ингест
читает уже компактные `data/graph/prepared/*.json`. Граница воспроизводимости:
сырьё (Drive, вне git) → prep (здесь) → prepared/ (в git, компактно) → граф.

Запуск: python3 seo-platform/graph_prep.py <RAW_DIR>
  RAW_DIR содержит: esco_x/esco-v1.2.1.json-ld, isco08.xlsx, okz.pdf
Выход: seo-platform/data/graph/prepared/{occupations,competencies,occupation_competency,okz_labels}.json
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "data" / "graph" / "prepared"


# Русские названия групп ISCO/ОКЗ, которые парсер ОКЗ пропустил (есть в
# МСКЗ-08, но строка не совпала с шаблоном). Названия — по номенклатуре ОКЗ.
OKZ_OVERRIDES = {
    "2120": "Математики, актуарии и статистики",
    "2513": "Разработчики Web и мультимедийных приложений",
    "3315": "Оценщики и эксперты по определению ущерба",
    "3435": "Иные специалисты-техники в области искусств и культуры",
    "3514": "Техники по Web-технологиям",
    "4414": "Писари и родственные работники",
    "5161": "Астрологи, гадалки и родственные работники",
    "6320": "Фермеры, ведущие натуральное животноводство",
    "6330": "Фермеры, ведущие натуральное смешанное сельское хозяйство",
    "6340": "Рыболовы, охотники и собиратели, ведущие натуральное хозяйство",
}


def load_isco(xlsx):
    import openpyxl
    wb = openpyxl.load_workbook(xlsx, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(c).strip() if c else "" for c in rows[0]]
    col = {name: hdr.index(name) for name in hdr}
    ci = col.get("ISCO 08 Code"); ct = col.get("Title EN")
    cd = col.get("Definition"); ck = col.get("Tasks include"); cl = col.get("Level")
    groups = {}
    for r in rows[1:]:
        if not r or r[ci] is None:
            continue
        code = str(r[ci]).strip()
        if not code.isdigit():
            continue
        groups[code] = {
            "code": code,
            "level": int(r[cl]) if r[cl] else len(code),
            "titleEn": (str(r[ct]).strip() if r[ct] else ""),
            "definitionEn": (str(r[cd]).strip() if cd is not None and r[cd] else ""),
            "tasksEn": (str(r[ck]).strip() if ck is not None and r[ck] else ""),
        }
    return groups


def load_okz_labels(pdf):
    """ОКЗ ОК 010-2014: русские названия начальных групп (4-значный код).
    Коды ОКЗ = коды ISCO-08 (МСКЗ-08). Берём строки «NNNN Наименование»."""
    import pypdf
    r = pypdf.PdfReader(pdf)
    text = []
    for pg in r.pages:
        t = pg.extract_text() or ""
        text.append(t)
    full = "\n".join(text)
    labels = {}
    # код из 4 цифр в начале строки + кириллическое наименование
    pat = re.compile(r"(?m)^\s*(\d{4})\s+([А-ЯЁ][А-Яа-яЁё \-,()«».]{4,120})\s*$")
    for m in pat.finditer(full):
        code, name = m.group(1), m.group(2).strip()
        # отбросить строки, где «наименование» — это продолжение таблицы (цифры/хвосты)
        if code not in labels and not re.search(r"\d", name):
            labels[code] = name
    for code, name in OKZ_OVERRIDES.items():
        labels.setdefault(code, name)
    return labels


def load_okz_examples(pdf):
    """«Примеры занятий» из ОКЗ ОК 010-2014 по каждой начальной группе (4 знака).
    Это авторитетные русские названия профессий внутри группы, из того же
    классификатора, что и сами группы — связь точная, без кроссволка."""
    import pypdf
    r = pypdf.PdfReader(pdf)
    lines = []
    for p in r.pages:
        lines += (p.extract_text() or "").split("\n")
    hdr = re.compile(r"^\s*(\d{4})\s+[А-ЯЁ]")
    headers = [(i, hdr.match(l).group(1)) for i, l in enumerate(lines) if hdr.match(l)]
    examples = {}
    for k, (idx, code) in enumerate(headers):
        end = headers[k + 1][0] if k + 1 < len(headers) else len(lines)
        block = lines[idx:end]
        pi = next((j for j, l in enumerate(block) if "Примеры занятий" in l), None)
        if pi is None:
            continue
        items = []
        for l in block[pi + 1:]:
            s = l.strip()
            if not s:
                continue
            # хвост «Некоторые родственные занятия…» и перекрёстные ссылки — не наши
            if "родственные занятия" in s or "отнесенные к другим" in s:
                break
            if re.match(r"^\d{4}\s", s):
                break
            if not re.search("[А-Яа-яЁё]", s):
                continue
            if s[0].islower() and items:  # склейка перенесённой строки
                items[-1] += " " + s
            else:
                items.append(s)
        # дедуп с сохранением порядка
        seen = []
        for x in items:
            if x not in seen:
                seen.append(x)
        if seen:
            examples[code] = seen[:40]
    return examples


def load_esco(jsonld):
    data = json.load(open(jsonld, "r", encoding="utf-8"))
    g = data["@graph"]

    def types(n):
        t = n.get("type")
        return t if isinstance(t, list) else [t]

    def label_en(n):
        pl = n.get("preferredLabel")
        # preferredLabel — список skosXl:Label (у каждого literalForm: {lang: str}).
        if isinstance(pl, list):
            for lab in pl:
                lf = lab.get("literalForm", {}) if isinstance(lab, dict) else {}
                if lf.get("en"):
                    return lf["en"]
            return ""
        if isinstance(pl, dict):
            return pl.get("literalForm", {}).get("en", "")
        return ""

    # навыки: uri -> {labelEn, skillType}
    skills = {}
    for n in g:
        if "esco:Skill" in types(n):
            skills[n["uri"]] = {
                "labelEn": label_en(n),
                "skillType": (n.get("skillType") or ""),
            }

    # профессии → ISCO4; агрегируем навыки по группе ISCO
    # occ_by_isco[isco4] = {"occCount", "escoLabels":set, "essential":Counter, "optional":Counter}
    from collections import Counter
    occ_by_isco = {}
    for n in g:
        if "esco:Occupation" not in types(n):
            continue
        notation = str(n.get("notation") or "")
        m = re.match(r"^(\d{4})", notation)
        if not m:
            continue
        isco4 = m.group(1)
        e = occ_by_isco.setdefault(isco4, {
            "occCount": 0, "escoLabels": [], "ess": Counter(), "opt": Counter()})
        e["occCount"] += 1
        lab = label_en(n)
        if lab:
            e["escoLabels"].append(lab)
        for s in (n.get("relatedEssentialSkill") or []):
            if s in skills:
                e["ess"][s] += 1
        for s in (n.get("relatedOptionalSkill") or []):
            if s in skills:
                e["opt"][s] += 1
    return skills, occ_by_isco


def main():
    raw = Path(sys.argv[1])
    OUT.mkdir(parents=True, exist_ok=True)

    isco = load_isco(raw / "isco08.xlsx")
    okz = load_okz_labels(raw / "okz.pdf")
    okz_examples = load_okz_examples(raw / "okz.pdf")
    esco_file = next((raw / "esco_x").glob("*.json-ld"))
    skills, occ_by_isco = load_esco(esco_file)

    # --- occupations.json : узлы-профессии = ISCO 4-значные группы
    occupations = []
    used_skills = set()
    occ_comp = []
    for code, meta in sorted(isco.items()):
        if meta["level"] != 4:
            continue
        agg = occ_by_isco.get(code)
        esco_labels = sorted(set(agg["escoLabels"]))[:60] if agg else []
        occupations.append({
            "isco4": code,
            "titleEn": meta["titleEn"],
            "definitionEn": meta["definitionEn"][:1200],
            "tasksEn": meta["tasksEn"][:1200],
            "labelRu": okz.get(code),  # может быть None
            "escoOccupationCount": (agg["occCount"] if agg else 0),
            "escoLabelsEn": esco_labels,
            "okzExamples": okz_examples.get(code, []),
            "parent3": code[:3],
        })
        if not agg or agg["occCount"] == 0:
            continue
        n = agg["occCount"]
        # компетенция включается, если essential хотя бы у одной профессии группы;
        # вес = доля профессий группы, где навык essential (0..1)
        weights = {}
        for s, c in agg["ess"].items():
            weights[s] = ("essential", round(c / n, 3))
        for s, c in agg["opt"].items():
            if s not in weights:  # essential приоритетнее
                weights[s] = ("optional", round(0.5 * c / n, 3))
        top = sorted(weights.items(), key=lambda kv: -kv[1][1])[:30]
        for s, (kind, w) in top:
            used_skills.add(s)
            occ_comp.append({"isco4": code, "skill": s, "kind": kind, "weight": w})

    competencies = [{"uri": u, **skills[u]} for u in sorted(used_skills)]

    (OUT / "occupations.json").write_text(json.dumps(occupations, ensure_ascii=False), encoding="utf-8")
    (OUT / "competencies.json").write_text(json.dumps(competencies, ensure_ascii=False), encoding="utf-8")
    (OUT / "occupation_competency.json").write_text(json.dumps(occ_comp, ensure_ascii=False), encoding="utf-8")
    (OUT / "okz_labels.json").write_text(json.dumps(okz, ensure_ascii=False), encoding="utf-8")

    ru = sum(1 for o in occupations if o["labelRu"])
    with_comp = len(set(o["isco4"] for o in occ_comp))
    print(f"occupations: {len(occupations)} (с рус. меткой ОКЗ: {ru}, с компетенциями: {with_comp})")
    print(f"competencies (ESCO, использованных): {len(competencies)}")
    print(f"occupation→competency рёбер: {len(occ_comp)}")
    print(f"ОКЗ русских меток всего распознано: {len(okz)}")


if __name__ == "__main__":
    main()
