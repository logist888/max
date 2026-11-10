#!/usr/bin/env python3
"""Зарплаты в раздел профессий — из авторитетного публикуемого госисточника (Росстат).

Источник: **Росстат**, обследование заработной платы работников по группам занятий
ОКЗ ОК 010-2014, **октябрь 2025** (Статбюлетень 2025.xlsx в data/graph/raw/). Берём:
- лист 6 — средняя ЗП по группам занятий, все формы собственности (1 и 2 знака ОКЗ);
- лист 9 — «составные группы ОКЗ» (3 знака) — детальный уровень;
- лист 31 — ЗП по группам занятий × субъектам РФ → строка «г. Москва» по 9 майор-группам.

Строки Росстата даны только русскими названиями (кодов нет) → сопоставляем имя→код
курируемым кроссволком app/config/graph/rosstat-okz-crosswalk.json (по стандарту ISCO-08).

По каждой из 436 профессий:
- avgRF = средняя по её группе занятий на самом детальном доступном уровне (3→2→1 знак), 2025;
- avgMoscow = avgRF × фактическая надбавка Москва/РФ по её майор-группе (из листа 31).
Индексация НЕ нужна (данные уже 2025). Итог — помеченная ОЦЕНКА по группе, не факт по должности.

hh.ru не используется (соглашение запрещает). «Работа России» (trudvsem) убрана (занижает).
Где группы нет в обследовании (военные 0xxx) — запись не создаётся → «Информация отсутствует».

Пишет data/graph/prepared/salary.json: {код ОКЗ (4 знака): {rosstat:{...}}}.
Запуск: python3 seo-platform/graph_salary.py <RETRIEVED_DATE>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PREP = ROOT / "data" / "graph" / "prepared"
XLSX = ROOT / "data" / "graph" / "raw" / "rosstat_srzpl_2025.xlsx"
CROSSWALK = ROOT / "app" / "config" / "graph" / "rosstat-okz-crosswalk.json"
PARAMS = ROOT / "app" / "config" / "graph" / "salary-params.json"
SANITY_MIN, SANITY_MAX = 10000, 3_000_000
LEVEL_NAME = {3: "составная группа ОКЗ (3 знака)", 2: "подгруппа ОКЗ (2 знака)", 1: "укрупнённая группа ОКЗ"}


def norm(s):
    return " ".join(str(s).split()).strip()


def sheet_name_wage(ws):
    """{нормализованное имя группы: средняя ЗП (столбец C)}."""
    out = {}
    for r in ws.iter_rows(values_only=True):
        nm = r[0]
        w = r[2] if len(r) > 2 else None
        if nm is None or not isinstance(w, (int, float)):
            continue
        if SANITY_MIN <= w <= SANITY_MAX:
            out[norm(nm)] = round(w)
    return out


def moscow_ratios(ws):
    """Из листа 31: надбавка Москва/РФ по майор-группам 1..9 (первое число — Всего)."""
    rf = mos = None
    for r in ws.iter_rows(values_only=True):
        if not r or r[0] is None:
            continue
        name = norm(r[0])
        nums = [x for x in r[1:] if isinstance(x, (int, float))]
        if name == "Российская Федерация":
            rf = nums
        elif name.replace("г.", "").strip() == "Москва":
            mos = nums
    if not rf or not mos:
        raise SystemExit("лист 31: не найдены строки РФ/Москва")
    # nums[0] = Всего, далее майоры 1..9
    return {str(i): mos[i] / rf[i] for i in range(1, 10)}


def main():
    when = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    occupations = json.load(open(PREP / "occupations.json", encoding="utf-8"))
    cw = json.load(open(CROSSWALK, encoding="utf-8"))
    params = json.load(open(PARAMS, encoding="utf-8"))
    base_date = params["base"]["period"]
    src = params["base"]["source"]

    if not XLSX.exists():
        (PREP / "salary.json").write_text("{}", encoding="utf-8")
        print(f"Нет {XLSX.name} — salary.json пуст (зарплата = «Информация отсутствует»).")
        return

    from openpyxl import load_workbook
    wb = load_workbook(XLSX, read_only=True, data_only=True)
    w6 = sheet_name_wage(wb["6"])
    w9 = sheet_name_wage(wb["9"])
    ratios = moscow_ratios(wb["31"])
    wb.close()

    # base{код ОКЗ: средняя ЗП РФ 2025}. 3 знака (л.9) приоритетнее; 2 и 1 знак — из л.6.
    base = {}
    miss = []
    for nm, code in cw["major"].items():
        if norm(nm) in w6: base[code] = w6[norm(nm)]
        else: miss.append(("major", nm))
    for nm, code in cw["sub2"].items():
        if norm(nm) in w6: base[code] = w6[norm(nm)]
        else: miss.append(("sub2", nm))
    for nm, code in cw["min3"].items():
        if norm(nm) in w9: base[code] = w9[norm(nm)]
        else: miss.append(("min3", nm))
    if miss:
        print(f"ВНИМАНИЕ: {len(miss)} имён кроссволка не найдено в листах:")
        for lvl, nm in miss[:15]:
            print(f"  [{lvl}] {nm}")

    def match(isco4):
        for n in (3, 2, 1):
            if isco4[:n] in base:
                return isco4[:n], n
        return None, 0

    salary = {}
    lvl_count = {1: 0, 2: 0, 3: 0, 0: 0}
    for o in occupations:
        isco4 = o["isco4"]
        code, n = match(isco4)
        lvl_count[n] += 1
        if not code:
            continue
        rf = base[code]
        major = isco4[0]
        ratio = ratios.get(major)
        moscow = round(rf * ratio) if ratio else None
        salary[isco4] = {
            "rosstat": {
                "avgRF": rf,
                "avgMoscow": moscow,
                "baseDate": base_date,
                "matchLevel": LEVEL_NAME[n],
                "matchCode": code,
                "moscowRatio": round(ratio, 3) if ratio else None,
                "moscowMajor": major,
                "currency": "RUB",
                "source": src,
                "retrievedAt": when,
            }
        }

    PREP.mkdir(parents=True, exist_ok=True)
    (PREP / "salary.json").write_text(json.dumps(salary, ensure_ascii=False), encoding="utf-8")
    print(f"salary.json: {len(salary)} занятий с зарплатой (Росстат окт-{base_date}). "
          f"Уровни: 3зн {lvl_count[3]}, 2зн {lvl_count[2]}, майор {lvl_count[1]}, нет данных {lvl_count[0]}.")
    print("Надбавки Москвы по майор-группам:", {k: round(v, 3) for k, v in ratios.items()})


if __name__ == "__main__":
    main()
