#!/usr/bin/env python3
"""Зарплаты в раздел профессий — из легальных госисточников (hh.ru запрещён его
соглашением). Пишет data/graph/prepared/salary.json: по коду группы ISCO/ОКЗ →
{rosstat:{...}, trudvsem:{...}}.

Источники:
- Работа России (trudvsem.ru) — открытый API, медиана предлагаемой зарплаты по
  вакансиям. Сопоставление по названиям занятий из ОКЗ (okzExamples) через
  текстовый поиск. Публиковать открытые госданные можно.
- Росстат (обследование по проф. группам ОКЗ) — авторитетная средняя; парсится
  из переданного файла, если он есть (rosstat_okz.* в raw-каталоге).

Запуск: python3 seo-platform/graph_salary.py <RETRIEVED_DATE> [RAW_DIR]
  RETRIEVED_DATE — дата выгрузки (ISO), напр. 2026-07-14 (для провенанса).
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import median

ROOT = Path(__file__).parent
PREP = ROOT / "data" / "graph" / "prepared"
TV = "https://opendata.trudvsem.ru/api/v1/vacancies"
UA = "MainExperts-eduplatform/1.0 (education profession catalog; contact: site owner)"
MIN_N = 5          # минимум вакансий с зарплатой, иначе не показываем
SANITY_MIN = 10000  # ₽/мес; ниже — мусор
SANITY_MAX = 1_500_000


def tv_query(term, limit=100):
    url = f"{TV}?text={urllib.parse.quote(term)}&limit={limit}&offset=0"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None


def salary_values(data):
    """Представительная месячная зарплата по вакансии: середина вилки, иначе min."""
    out = {}
    if not data:
        return out
    for x in (data.get("results", {}) or {}).get("vacancies", []) or []:
        v = x.get("vacancy", {})
        vid = v.get("id")
        cur = (v.get("currency") or "").strip("«»")
        if cur and cur not in ("руб.", "RUR", "RUB", "руб"):
            continue  # только рубли
        lo = v.get("salary_min") or 0
        hi = v.get("salary_max") or 0
        val = (lo + hi) / 2 if (lo and hi and hi >= lo) else (lo or hi)
        if val and SANITY_MIN <= val <= SANITY_MAX and vid:
            out[vid] = val
    return out


def pick_term(o):
    """Один представительный запрос на занятие: самое короткое название-пример
    (обычно базовое, напр. «Бухгалтер»), иначе имя группы."""
    ex = o.get("okzExamples") or []
    return min(ex, key=len) if ex else (o.get("labelRu") or "")


def load_trudvsem(occupations, when):
    tasks = [(o["isco4"], pick_term(o)) for o in occupations if pick_term(o)]
    n = len(tasks)

    def work(item):
        isco, term = item
        return isco, term, salary_values(tv_query(term))

    result = {}
    done = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        for isco, term, vals in pool.map(work, tasks):
            done += 1
            nums = sorted(vals.values())
            if len(nums) >= MIN_N:
                result[isco] = {
                    "median": round(median(nums)),
                    "p25": round(nums[len(nums) // 4]),
                    "p75": round(nums[(3 * len(nums)) // 4]),
                    "count": len(nums),
                    "currency": "RUB",
                    "kind": "предлагаемая по вакансиям",
                    "source": "Работа России (trudvsem.ru)",
                    "retrievedAt": when,
                    "term": term,
                }
            if done % 50 == 0:
                print(f"  trudvsem: {done}/{n}, с зарплатой {len(result)}", flush=True)
    return result


def load_rosstat(raw_dir):
    """Средняя по проф. группам ОКЗ из файла Росстата, если он передан.
    Пока файла нет — возвращаем пусто (владелец дозаливает; парсер добавим по факту)."""
    if not raw_dir:
        return {}
    cand = list(Path(raw_dir).glob("rosstat_okz*"))
    if not cand:
        return {}
    # Формат файла Росстата подтвердим по факту получения; заглушка не выдумывает.
    print(f"  Росстат: найден файл {cand[0].name} — парсер добавим под его формат")
    return {}


def main():
    when = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    raw_dir = sys.argv[2] if len(sys.argv) > 2 else None
    occupations = json.load(open(PREP / "occupations.json", encoding="utf-8"))
    print(f"занятий: {len(occupations)}; тяну trudvsem (дата {when})…", flush=True)

    trudvsem = load_trudvsem(occupations, when)
    rosstat = load_rosstat(raw_dir)

    salary = {}
    for code in set(trudvsem) | set(rosstat):
        salary[code] = {}
        if code in rosstat:
            salary[code]["rosstat"] = rosstat[code]
        if code in trudvsem:
            salary[code]["trudvsem"] = trudvsem[code]

    (PREP / "salary.json").write_text(json.dumps(salary, ensure_ascii=False), encoding="utf-8")
    print(f"salary.json: {len(salary)} занятий с зарплатой "
          f"(trudvsem {len(trudvsem)}, rosstat {len(rosstat)})")


if __name__ == "__main__":
    main()
