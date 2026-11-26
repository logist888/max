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
GBUDGET = HSE / "rating_102339002.html"  # вуз × укрупнённая группа × бюджет
GPAID = HSE / "rating_102339030.html"    # вуз × укрупнённая группа × платно
YEAR = 2025

# Аббревиатуры раскрываем ТОЛЬКО с обязательной точкой — иначе «гос.»-паттерн
# съедает начало полных слов («государственное» → «государственный…»). Дефисные
# формы (ун-т./ин-т.) безопасны (полные слова без дефиса не совпадут).
ABBR = [
    (r'\bгос\.', 'государственный '), (r'\bун-т[а-я]*\.?', 'университет '),
    (r'\bин-т[а-я]*\.?', 'институт '), (r'\bнац\.', 'национальный '),
    (r'\bиссл\.', 'исследовательский '), (r'\bагротехнол\.', 'агротехнологический '),
    (r'\bполитехн\.', 'политехнический '),
    # «технол.»/«техн.» без ведущего \b — ловят и слитные композиты (лесотехн., электротехн.,
    # радиотехн., биотехнол.): обязательная точка не даёт задеть полные слова. Дефисные формы
    # (физико-техн., химико-технол.) и так раскрываются через границу на дефисе.
    (r'технол\.', 'технологический '), (r'техн\.', 'технический '),
    (r'\bпед\.', 'педагогический '),
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


def parse_group(path, score_col, n_col=None):
    """[(группа, вузName, балл, n)] из таблицы вуз×укрупнённая группа."""
    h = path.read_text(encoding="utf-8", errors="replace")
    big = max(re.findall(r'<table.*?</table>', h, re.S), key=len)
    out = []
    for r in re.findall(r'<tr.*?</tr>', big, re.S):
        cells = [html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', c)).strip())
                 for c in re.findall(r'<t[dh].*?</t[dh]>', r, re.S)]
        if len(cells) <= score_col:
            continue
        group, vuz = cells[0], cells[1]
        try:
            score = float(cells[score_col].replace(',', '.'))
        except ValueError:
            continue
        if not group or not vuz or not (30 <= score <= 100):
            continue
        n = None
        if n_col is not None and len(cells) > n_col:
            try:
                n = int(re.sub(r'\D', '', cells[n_col]) or 0)
            except ValueError:
                n = None
        out.append((group, vuz, score, n))
    return out


# Профильный тип вуза — главный различитель со-городних вузов (мед/техн/аграрный…).
# Матч разрешаем только при СОВПАДЕНИИ набора профильных типов: «медицинский» матчит
# «медицинский», классический (без типа) — только классический. Иначе Алтайский ГМУ
# ложно матчился на Алтайский ГУ (Jaccard выше у более короткого классического имени).
TYPE_TOKENS = {
    "медицинский", "технический", "технологический", "агротехнологический", "аграрный",
    "педагогический", "экономический", "гуманитарный", "архитектурный", "политехнический",
    "лингвистический", "юридический", "транспортный", "аэрокосмический", "промышленный",
    "горный", "лесотехнический", "лесной", "морской", "ветеринарный", "путей", "физической",
    "электротехнический", "авиационный", "радиотехнический", "энергетический", "строительный",
    "инженерный", "финансовый", "социальный", "культуры", "искусств", "геологоразведочный",
    "химико", "текстильный", "полиграфический", "музыкальный", "театральный", "художественный",
}


def jac(a, b):
    return (len(a & b) / len(a | b)) if (a and b) else 0.0


def build_matcher(ours):
    """Мемоизированный матч имени вуза ВШЭ → (slug, name, jaccard, inter) или None.

    Считаем Jaccard против ДВУХ вариантов нашего названия и берём максимум:
    - полное описательное (ловит головные вузы: «Адыгейский государственный университет»);
    - краткое (ловит филиалы с акронимом: «Алтайский филиал РАНХиГС»).
    Точность: требуем ≥2 общих токена; если у ВШЭ нет города для фильтра — порог строже."""
    memo = {}

    def match(hname):
        if hname in memo:
            return memo[hname]
        hcity, htok = city_of(hname), tokens(name_wo_city(hname))
        if not hcity:   # подсказка города из аббревиатур без «, г. X» (Моск./С.-Петерб.)
            nl = norm(hname)
            if "моск" in nl:
                hcity = "москва"
            elif "петерб" in nl or "спб" in nl:
                hcity = "санкт петербург"
        htypes = htok & TYPE_TOKENS
        best, best_j, best_int = None, 0.0, 0
        for o in ours:
            if hcity and o["city"] and hcity != o["city"]:
                continue
            if o["types"] != htypes:   # профильный тип должен совпасть (мед≠классич.)
                continue
            j = max(jac(htok, o["tok"]), jac(htok, o["tokShort"]))
            if j > best_j:
                inter = max(len(htok & o["tok"]), len(htok & o["tokShort"]))
                best_j, best, best_int = j, o, inter
        thr = 0.5 if hcity else 0.67   # без города — строже (защита от ложных)
        ok = best and best_j >= thr and best_int >= 2
        res = (best["slug"], best["name"], round(best_j, 2), best_int) if ok else None
        memo[hname] = res
        return res

    return match


def main():
    catalog = json.load(open(CATALOG, encoding="utf-8"))
    # Полное описательное название вуза — из org-cards (shortName у нас часто акроним
    # «АГУ», HSE даёт описательное «Адыгейский гос. ун-т.» → матч только по полному имени).
    orgname = {}
    for o in json.load(open(ORGCARDS, encoding="utf-8")):
        orgname[o["id"]] = o.get("name") or o.get("fullName") or o.get("shortName", "")
    ours = []
    for c in catalog:
        full = orgname.get(c["id"], c.get("shortName", ""))
        tok = tokens(full)
        ours.append({
            "slug": c["slug"], "name": full, "city": norm(c.get("cityName", "")),
            "tok": tok,                                  # полное описательное
            "tokShort": tokens(c.get("shortName", "")),  # краткое (акронимы филиалов)
            "types": tok & TYPE_TOKENS,                  # профильный тип для гварда
        })
    match = build_matcher(ours)

    # --- Уровень вуза (бюджет + платно) ---
    budget, paid = parse_table(BUDGET, 1, 3), parse_table(PAID, 1, 3)
    hse = {}
    for name, d in budget.items():
        hse[name] = {"budget": d["score"], "nBudget": d["n"], "paid": None}
    for name, d in paid.items():
        hse.setdefault(name, {"budget": None, "nBudget": None, "paid": None})
        hse[name]["paid"] = d["score"]

    scores, report = {}, {"matched": [], "unmatched": []}
    for hname, d in hse.items():
        m = match(hname)
        if m:
            scores[m[0]] = {"budget": d["budget"], "paid": d["paid"], "nBudget": d["nBudget"],
                            "year": YEAR, "hseName": hname}
            report["matched"].append({"hse": hname, "our": m[1], "j": m[2]})
        else:
            report["unmatched"].append({"hse": hname, "bestJ": 0})

    # --- Уровень вуз × укрупнённая группа (классификация ВШЭ) ---
    bygroup = {}   # slug -> {группа: {budget, paid, nBudget}}
    for group, vuz, score, n in parse_group(GBUDGET, 2, 4):
        m = match(vuz)
        if not m:
            continue
        g = bygroup.setdefault(m[0], {}).setdefault(group, {"budget": None, "paid": None, "nBudget": None})
        g["budget"], g["nBudget"] = score, n
    for group, vuz, score, n in parse_group(GPAID, 2):
        m = match(vuz)
        if not m:
            continue
        g = bygroup.setdefault(m[0], {}).setdefault(group, {"budget": None, "paid": None, "nBudget": None})
        g["paid"] = score
    by_group_out = {
        slug: sorted(
            [{"group": g, **v} for g, v in gs.items()],
            key=lambda x: -(x["budget"] or x["paid"] or 0),
        ) for slug, gs in bygroup.items()
    }

    (HSE / "hse-scores.json").write_text(json.dumps(scores, ensure_ascii=False, indent=1), encoding="utf-8")
    (HSE / "hse-scores-by-group.json").write_text(json.dumps(by_group_out, ensure_ascii=False), encoding="utf-8")
    (HSE / "match-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Уровень вуза: сматчено {len(scores)} (не сматчено {len(report['unmatched'])}).")
    print(f"Уровень вуз×группа: {len(by_group_out)} вузов, "
          f"{sum(len(v) for v in by_group_out.values())} строк вуз-группа.")


if __name__ == "__main__":
    main()
