# -*- coding: utf-8 -*-
"""Аудит выгрузки базы вузов (universities_master_*.csv).

Каждый факт из seo-platform/00-audit.md воспроизводится этим скриптом.
Запуск: python3 seo-platform/audit_csv.py <путь к csv>

Проверяет: объём и заполненность колонок; корректность JSON в колонке
programs; обрезку поля на лимите экспорта; расхождение заявленного числа
направлений с фактическим; нормализацию городов; пропуски стоимости.
"""
import collections
import csv
import hashlib
import json
import re
import sys

csv.field_size_limit(sys.maxsize)


def main(path):
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    cols = list(rows[0].keys())
    print(f"Файл: {path}\nsha256: {digest}\nСтрок: {len(rows)}, колонок: {len(cols)}\n")

    print("=== Заполненность колонок ===")
    for c in cols:
        filled = sum(1 for r in rows if (r.get(c) or "").strip() not in ("", "null", "None"))
        print(f"{filled:5d} ({100 * filled / len(rows):5.1f}%)  {c}")

    print("\n=== География ===")
    regions = collections.Counter((r["region"] or "").strip() for r in rows)
    cities = collections.Counter((r["city"] or "").strip() for r in rows)
    print(f"Регионов: {len(regions)}, сырых значений города: {len(cities)}")

    def norm_city(c):
        return re.sub(r"^(г\.|город|пос\.|п\.|с\.|пгт\.?|рп\.?|ст-ца|дер\.|д\.)\s*",
                      "", c, flags=re.I).strip().lower()

    groups = collections.defaultdict(list)
    for c in cities:
        groups[norm_city(c)].append(c)
    collisions = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Городов после нормализации: {len(groups)}, групп с разночтениями: {len(collisions)}")
    foreign = sum(1 for r in rows if "иностранного" in (r["region"] or ""))
    branches = sum(1 for r in rows if "филиал" in (r["name"] or "").lower())
    print(f"Зарубежных записей: {foreign}, записей-филиалов (по названию): {branches}")

    print("\n=== Программы (JSON в колонке programs) ===")
    ok_records = 0
    truncated = []          # (id, shortName, длина поля, заявлено направлений, записей в обрезке)
    declared_mismatch = 0
    declared_checked = 0
    paid_total = paid_no_cost = 0
    okso = set()
    rec_re = re.compile(r'\{"okso":')
    for r in rows:
        p = (r.get("programs") or "").strip()
        if not p:
            continue
        try:
            declared = int(r.get("indicators.Направлений подготовки") or "")
        except ValueError:
            declared = None
        try:
            arr = json.loads(p)
        except json.JSONDecodeError:
            truncated.append((r["id"], r["shortName"], len(p), declared,
                              len(rec_re.findall(p))))
            continue
        ok_records += len(arr)
        if declared is not None:
            declared_checked += 1
            if declared != len(arr):
                declared_mismatch += 1
        for it in arr:
            if it.get("okso"):
                okso.add(it["okso"])
            if it.get("placeType") == "Платные места":
                paid_total += 1
                if not it.get("cost"):
                    paid_no_cost += 1
    print(f"Корректных записей программ: {ok_records}, уникальных кодов ОКСО: {len(okso)}")
    print(f"Платных записей: {paid_total}, из них без стоимости: {paid_no_cost} "
          f"({100 * paid_no_cost / max(1, paid_total):.1f}%)")
    print(f"Вузов с расхождением «заявлено направлений ≠ записей»: "
          f"{declared_mismatch} из {declared_checked} проверенных")

    print(f"\n=== Обрезка поля programs: {len(truncated)} вузов ===")
    if truncated:
        lens = sorted(t[2] for t in truncated)
        print(f"Длины повреждённых полей: min {lens[0]}, max {lens[-1]} "
              f"(лимит экспорта ~30 000 символов)")
        total_declared = sum(t[3] or 0 for t in truncated)
        total_found = sum(t[4] for t in truncated)
        print(f"Заявлено записей у повреждённых: {total_declared}, физически в файле: "
              f"{total_found}, потеряно: {total_declared - total_found} "
              f"({100 * (total_declared - total_found) / max(1, total_declared):.0f}%)")
        by_declared = sorted(truncated, key=lambda t: t[3] or 0, reverse=True)
        print("Топ-10 пострадавших по заявленному объёму:")
        for t in by_declared[:10]:
            print(f"  заявлено {t[3]}, в файле {t[4]}  | {t[1][:60]}")


if __name__ == "__main__":
    main(sys.argv[1])
