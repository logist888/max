#!/usr/bin/env python3
"""Парсер перечня вступительных испытаний → маппинг «направление (ОКСО) → предметы ЕГЭ».

Источник (нормативный, публичный): Приказ Минобрнауки № 820 от 27.11.2024 (ред. № 904 от
26.11.2025) «Перечень вступительных испытаний при приёме на программы бакалавриата и
специалитета». Сохранён как data/ege/perechen-820-source.html (выгрузка rulaws.ru).

Русский язык — обязателен для всех (Раздел 1), в набор не включаем как различающий признак.
Для каждого направления собираем множество допустимых предметов (профильный + по выбору),
которое вуз использует по своим правилам приёма. Это уровень направления, не вуза.

Выход: data/ege/ege-subjects.json = {"meta": {...}, "subjects": {"<ОКСО 6 знаков>": [предметы]}}
Запуск: python3 scripts/build_ege_map.py
"""
import re
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "ege" / "perechen-820-source.html"
OUT = ROOT / "data" / "ege" / "ege-subjects.json"

SUBJ_MAP = [
    ("обществознание", "обществознание"), ("биологи", "биология"), ("хими", "химия"),
    ("истори", "история"), ("информатик", "информатика"), ("физик", "физика"),
    ("географи", "география"), ("литератур", "литература"), ("иностранн", "иностранный язык"),
    ("математик", "математика"), ("русский", "русский язык"),
]
CODE_RE = re.compile(r'^(\d{2}\.\d{2}\.\d{2})\s+(.+)')
UGS_RE = re.compile(r'^(\d{2})\.00\.00\b')


def clean(t):
    t = re.sub(r'<[^>]+>', ' ', t)
    return html.unescape(re.sub(r'\s+', ' ', t)).strip()


def as_subject(t):
    tl = t.lower()
    if "испытание" in tl or "раздел" in tl or len(t) > 60:
        return None
    for key, canon in SUBJ_MAP:
        if tl == canon or tl.startswith(key) or key in tl:
            return canon
    return None


def main():
    raw = SRC.read_text(encoding="utf-8", errors="replace")
    cells = [clean(d) for d in re.findall(r'<div[^>]*>(.*?)</div>', raw, re.S)]

    mapping, names = {}, {}
    cur_codes, cur_subj, seen_subj = [], set(), False

    def flush():
        nonlocal cur_codes, cur_subj, seen_subj
        if cur_codes and cur_subj:
            for c in cur_codes:
                mapping.setdefault(c, set()).update(cur_subj)
        cur_codes, cur_subj, seen_subj = [], set(), False

    for t in cells:
        if not t:
            continue
        if UGS_RE.match(t):
            flush(); continue
        m = CODE_RE.match(t)
        if m:
            if seen_subj:
                flush()
            cur_codes.append(m.group(1)); names[m.group(1)] = m.group(2)
            continue
        s = as_subject(t)
        if s and cur_codes:
            cur_subj.add(s); seen_subj = True
    flush()

    subjects = {c: sorted(s) for c, s in sorted(mapping.items())}
    data = {
        "meta": {
            "source": "Приказ Минобрнауки России № 820 от 27.11.2024 (ред. № 904 от 26.11.2025), "
                      "Перечень вступительных испытаний (бакалавриат/специалитет)",
            "sourceUrl": "http://publication.pravo.gov.ru/document/0001202411290027",
            "note": "Русский язык обязателен для всех направлений (в набор не включён как различающий). "
                    "Уровень направления, не вуза; конкретный набор определяют правила приёма вуза.",
            "directions": len(subjects),
        },
        "subjects": subjects,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ege-subjects.json: {len(subjects)} направлений (ОКСО) с предметами")


if __name__ == "__main__":
    main()
