#!/usr/bin/env python3
"""Средний балл ЕГЭ зачисленных (ВШЭ, Мониторинг качества приёма, 2025) → наши вузы.

ВАЖНО: это СРЕДНИЙ балл зачисленных, НЕ проходной. Источник — ВШЭ (ege.hse.ru),
серверно-отрендеренные таблицы рейтинга (сохранены в data/hse/rating_*.html).

У ВШЭ и у нас нет общего ID (ИНН) → связка фаззи: по городу + пересечению токенов
нормализованного названия. Берём ТОЛЬКО высококонфидентные матчи; остальное — без балла
(на странице «Информация отсутствует»). Отчёт связки — data/hse/match-report.json.

Выход: data/hse/hse-scores.json = {slug_нашего_вуза: {budget, paid, nBudget, year, hseName}}
Запуск: python3 scripts/build_hse_scores.py
"""
import re
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HSE = ROOT / "data" / "hse"
CATALOG = ROOT / "app" / "build" / "catalog-rows.json"
ORGCARDS = ROOT / "app" / "build" / "org-cards.json"  # полное описательное название вуза
BUDGET = HSE / "rating_102338950.html"   # вузы × бюджет
PAID = HSE / "rating_102338975.html"     # вузы × платно (+ балл бюджета в кол.5)
YEAR = 2025

# Аббревиатуры раскрываем ТОЛЬКО с обязательной точкой — иначе «гос.»-паттерн
# съедает начало полных слов («государственное» → «государственный…»). Дефисные
# формы (ун-т./ин-т.) безопасны (полные слова без дефиса не совпадут).
ABBR = [
    (r'\bгос\.', 'государственный '), (r'\bун-т[а-я]*\.?', 'университет '),
    (r'\bин-т[а-я]*\.?', 'институт '), (r'\bнац\.', 'национальный '),
    (r'\bиссл\.', 'исследовательский '), (r'\bтехнол\.', 'технологический '),
    (r'\bтехн\.', 'технический '), (r'\bпед\.', 'педагогический '),
    (r'\bмед\.', 'медицинский '), (r'\bэконом\.', 'экономический '),
    (r'\bакад\.', 'академия '), (r'\bпром\.', 'промышленный '),
    (r'\bагр\.', 'аграрный '), (r'\bархит\.', 'архитектурный '),
    (r'\bгуманит\.', 'гуманитарный '),
]
STOP = {'имени', 'им', 'фгбоу', 'фгаоу', 'во', 'во-', 'высшего', 'образования',
        'учреждение', 'образовательное', 'федеральное', 'государственное',
        'бюджетное', 'автономное', 'и', 'the'}


def norm(s):
    s = html.unescape(s).lower().replace('ё', 'е')
    s = re.sub(r'«|»|"|"|"', ' ', s)
    for pat, rep in ABBR:
        s = re.sub(pat, rep, s)
    s = re.sub(r'[^а-яa-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def tokens(s):
    return {t for t in norm(s).split() if t not in STOP and len(t) > 2}


def parse_table(path, score_col, n_col=None):
    h = path.read_text(encoding="utf-8", errors="replace")
    big = max(re.findall(r'<table.*?</table>', h, re.S), key=len)
    out = {}
    for r in re.findall(r'<tr.*?</tr>', big, re.S):
        cells = [html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', c)).strip())
                 for c in re.findall(r'<t[dh].*?</t[dh]>', r, re.S)]
        if len(cells) <= score_col:
            continue
        name = cells[0]
        try:
            score = float(cells[score_col].replace(',', '.'))
        except ValueError:
            continue
        if not (30 <= score <= 100):
            continue
        n = None
        if n_col is not None and len(cells) > n_col:
            try:
                n = int(re.sub(r'\D', '', cells[n_col]) or 0)
            except ValueError:
                n = None
        out[name] = {"score": score, "n": n}
    return out


def city_of(hse_name):
    m = re.search(r',\s*г\.?\s*([А-Яа-яЁё\- ]+)$', hse_name)
    return norm(m.group(1)) if m else ''


def name_wo_city(hse_name):
    return re.sub(r',\s*г\.?\s*[А-Яа-яЁё\- ]+$', '', hse_name)


def main():
    budget = parse_table(BUDGET, 1, 3)
    paid = parse_table(PAID, 1, 3)
    # объединяем вузы
    hse = {}
    for name, d in budget.items():
        hse[name] = {"budget": d["score"], "nBudget": d["n"], "paid": None}
    for name, d in paid.items():
        hse.setdefault(name, {"budget": None, "nBudget": None, "paid": None})
        hse[name]["paid"] = d["score"]
    print(f"ВШЭ: вузов с баллом — бюджет {len(budget)}, платно {len(paid)}, объединённо {len(hse)}")

    catalog = json.load(open(CATALOG, encoding="utf-8"))
    # Полное описательное название вуза — из org-cards (shortName у нас часто акроним
    # «АГУ», HSE даёт описательное «Адыгейский гос. ун-т.» → матч только по полному имени).
    orgname = {}
    for o in json.load(open(ORGCARDS, encoding="utf-8")):
        orgname[o["id"]] = o.get("name") or o.get("fullName") or o.get("shortName", "")
    ours = []
    for c in catalog:
        full = orgname.get(c["id"], c.get("shortName", ""))
        ours.append({
            "slug": c["slug"], "name": full,
            "city": norm(c.get("cityName", "")), "tok": tokens(full),
        })

    scores, report = {}, {"matched": [], "unmatched": []}
    for hname, d in hse.items():
        hcity = city_of(hname)
        htok = tokens(name_wo_city(hname))
        best, best_j = None, 0.0
        for o in ours:
            if hcity and o["city"] and hcity != o["city"]:
                continue
            if not o["tok"] or not htok:
                continue
            j = len(htok & o["tok"]) / len(htok | o["tok"])
            if j > best_j:
                best_j, best = j, o
        if best and best_j >= 0.5:   # высококонфидентно
            scores[best["slug"]] = {
                "budget": d["budget"], "paid": d["paid"], "nBudget": d["nBudget"],
                "year": YEAR, "hseName": hname,
            }
            report["matched"].append({"hse": hname, "our": best["name"], "j": round(best_j, 2)})
        else:
            report["unmatched"].append({"hse": hname, "bestJ": round(best_j, 2)})

    # дедуп: если два ВШЭ-вуза сматчились в один slug, оставляем лучший по Jaccard
    (HSE / "hse-scores.json").write_text(json.dumps(scores, ensure_ascii=False, indent=1), encoding="utf-8")
    (HSE / "match-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Сматчено высококонфидентно: {len(scores)} наших вузов; не сматчено ВШЭ-строк: {len(report['unmatched'])}")
    print("Примеры матчей:")
    for m in report["matched"][:8]:
        print(f"  [{m['j']}] ВШЭ «{m['hse'][:40]}» → наш «{m['our'][:40]}»")
    print("Примеры НЕ сматченных ВШЭ:")
    for u in report["unmatched"][:6]:
        print(f"  [{u['bestJ']}] {u['hse'][:60]}")


if __name__ == "__main__":
    main()
