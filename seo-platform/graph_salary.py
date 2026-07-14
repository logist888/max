#!/usr/bin/env python3
"""Зарплаты в раздел профессий — из авторитетного публикуемого госисточника.

Источник: **Росстат**, обследование заработной платы по профессиональным группам
ОКЗ ОК 010-2014 (окт-2023) — средняя начисленная по группе, по РФ. Ложится на наши
группы ОКЗ. К последнему опубликованному уровню приводим официальной индексацией
(рост средней зарплаты РФ), Москву — официальным коэффициентом Москва/РФ. Параметры —
в app/config/graph/salary-params.json (прозрачно, обновляемо).

Итоговые avgRF/avgMoscow — ПОМЕЧЕННАЯ ОЦЕНКА (источник+метод+дата), не точный факт по
каждой группе: оба коэффициента единые для всех групп. Правило проекта «не выдумывать»
соблюдено — база авторитетна, метод раскрыт, где данных нет → запись не создаётся.

hh.ru не используется (соглашение запрещает хранить/показывать данные на стороннем
коммерческом сайте — licenses: hh-api=blocked). «Работа России» (trudvsem) убрана:
портал центров занятости системно занижает (даже Москва в ~3 раза ниже рынка).

Пишет data/graph/prepared/salary.json: {код ОКЗ (4 знака): {rosstat:{...}}}.

Запуск: python3 seo-platform/graph_salary.py <RETRIEVED_DATE> [RAW_DIR]
  RETRIEVED_DATE — дата выгрузки (ISO), напр. 2026-07-14 (для провенанса).
  RAW_DIR — каталог с файлом Росстата (по умолчанию data/graph/raw). Нет файла → пусто.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PREP = ROOT / "data" / "graph" / "prepared"
PARAMS_PATH = ROOT / "app" / "config" / "graph" / "salary-params.json"
DEFAULT_RAW = ROOT / "data" / "graph" / "raw"
SANITY_MIN = 10000     # ₽/мес; ниже — мусор/ошибка единиц
SANITY_MAX = 2_000_000

LEVEL_NAME = {4: "4-знак ОКЗ", 3: "3-знак ОКЗ", 2: "2-знак ОКЗ", 1: "1-знак ОКЗ"}


def load_params():
    return json.load(open(PARAMS_PATH, encoding="utf-8"))


def _norm_code(raw):
    """Код ОКЗ из ячейки: только цифры, без точек/пробелов; иначе None."""
    s = "".join(ch for ch in str(raw) if ch.isdigit())
    return s if 1 <= len(s) <= 4 else None


def _norm_avg(raw):
    """Средняя зарплата из ячейки → float в разумных пределах, иначе None."""
    if raw is None:
        return None
    s = str(raw).replace("\xa0", "").replace(" ", "").replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        return None
    return v if SANITY_MIN <= v <= SANITY_MAX else None


def load_rosstat_base(raw_dir):
    """Средняя по группам ОКЗ из файла Росстата → {код ОКЗ: avg}.

    Порядок предпочтения (первый найденный):
    1. rosstat_okz.json — нормализованный {код: avg} или {код: {avg, ...}} (я контролирую);
    2. rosstat_okz.csv  — строки code,avg[,...] (заголовок допускается);
    3. rosstat_okz.xlsx — исходник Росстата, best-effort через openpyxl (эвристика:
       столбец кодов ОКЗ + соседний числовой столбец средней зарплаты).
    Нет файла — {} (Шаг 1: зарплата на страницах = «Информация отсутствует»).
    """
    d = Path(raw_dir) if raw_dir else DEFAULT_RAW
    if not d.exists():
        return {}, None

    js = sorted(d.glob("rosstat_okz*.json"))
    if js:
        raw = json.load(open(js[0], encoding="utf-8"))
        out = {}
        for k, v in raw.items():
            code = _norm_code(k)
            avg = _norm_avg(v.get("avg") if isinstance(v, dict) else v)
            if code and avg:
                out[code] = avg
        print(f"  Росстат: {js[0].name} → {len(out)} групп")
        return out, js[0].name

    cs = sorted(d.glob("rosstat_okz*.csv"))
    if cs:
        out = {}
        with open(cs[0], encoding="utf-8-sig", newline="") as f:
            for row in csv.reader(f):
                if len(row) < 2:
                    continue
                code, avg = _norm_code(row[0]), _norm_avg(row[1])
                if code and avg:
                    out[code] = avg
        print(f"  Росстат: {cs[0].name} → {len(out)} групп")
        return out, cs[0].name

    xl = sorted(d.glob("rosstat_okz*.xlsx"))
    if xl:
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            print(f"  Росстат: найден {xl[0].name}, но нет openpyxl — "
                  f"нормализуйте в rosstat_okz.json/.csv")
            return {}, xl[0].name
        out = _parse_xlsx(xl[0])
        print(f"  Росстат: {xl[0].name} → {len(out)} групп (best-effort xlsx)")
        return out, xl[0].name

    return {}, None


def _parse_xlsx(path):
    """Эвристический разбор исходника Росстата: в каждой строке ищем ячейку-код ОКЗ
    и первую числовую ячейку-зарплату правее неё. Формат подтверждается по факту
    получения файла; при сомнении — нормализовать вручную в rosstat_okz.json."""
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True, data_only=True)
    out = {}
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            code = avg = code_i = None
            for i, cell in enumerate(row):
                if code is None:
                    c = _norm_code(cell)
                    # код ОКЗ: чистая числовая строка длиной 1..4, не сама зарплата
                    if c and cell is not None and str(cell).strip() == c:
                        code, code_i = c, i
                    continue
                if i > code_i:
                    a = _norm_avg(cell)
                    if a:
                        avg = a
                        break
            if code and avg and (code not in out):
                out[code] = avg
    wb.close()
    return out


def match_code(isco4, base):
    """Самый специфичный код Росстата для нашей 4-значной группы: 4→3→2→1 по префиксу."""
    for n in (4, 3, 2, 1):
        pref = isco4[:n]
        if pref in base:
            return pref, n
    return None, 0


def build_salary(occupations, base, params, when):
    idx = params["indexFactor"]["value"]
    mos = params["moscowCoef"]["value"]
    indexed_to = params["indexFactor"]["targetPeriod"]
    base_date = params["base"]["period"]
    salary = {}
    for o in occupations:
        isco4 = o["isco4"]
        code, level = match_code(isco4, base)
        if not code:
            continue
        avg_base = round(base[code])
        avg_rf = round(avg_base * idx)
        salary[isco4] = {
            "rosstat": {
                "avgBase": avg_base,
                "baseDate": base_date,
                "avgRF": avg_rf,
                "avgMoscow": round(avg_rf * mos),
                "indexedTo": indexed_to,
                "indexFactor": idx,
                "moscowCoef": mos,
                "matchLevel": LEVEL_NAME[level],
                "matchCode": code,
                "currency": "RUB",
                "source": "Росстат, обследование по проф. группам ОКЗ (ОК 010-2014)",
                "retrievedAt": when,
            }
        }
    return salary


def main():
    when = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    raw_dir = sys.argv[2] if len(sys.argv) > 2 else None
    occupations = json.load(open(PREP / "occupations.json", encoding="utf-8"))
    params = load_params()
    base, fname = load_rosstat_base(raw_dir)
    if not base:
        print("Файла Росстата нет — salary.json пуст (зарплата = «Информация отсутствует»). "
              "Залейте rosstat_okz.json/.csv/.xlsx в data/graph/raw и перезапустите.")

    salary = build_salary(occupations, base, params, when) if base else {}
    PREP.mkdir(parents=True, exist_ok=True)
    (PREP / "salary.json").write_text(json.dumps(salary, ensure_ascii=False), encoding="utf-8")
    print(f"salary.json: {len(salary)} занятий с зарплатой "
          f"(источник Росстат{f', файл {fname}' if fname else ''}; "
          f"индекс ×{params['indexFactor']['value']}, Москва ×{params['moscowCoef']['value']})")


if __name__ == "__main__":
    main()
