# -*- coding: utf-8 -*-
"""Аудит JSON-выгрузки базы вузов (universities_master_*.json).

Продолжение audit_csv.py: проверяет пересобранный экспорт и, если передан
второй аргумент (старый CSV), сверяет повузово, что записи не потерялись.
Запуск: python3 seo-platform/audit_json.py <файл.json> [старый.csv]
"""
import collections
import csv
import hashlib
import json
import sys

csv.field_size_limit(sys.maxsize)


def main(path, csv_path=None):
    raw = open(path, "rb").read()
    print(f"Файл: {path}\nsha256: {hashlib.sha256(raw).hexdigest()}\nБайт: {len(raw)}")
    data = json.loads(raw.decode("utf-8-sig"))
    print(f"JSON валиден. Организаций: {len(data)}")
    ids = collections.Counter(u["id"] for u in data)
    assert not [k for k, v in ids.items() if v > 1], "дубли id"

    total = 0
    no_prog = []
    levels = collections.Counter()
    okso = set()
    paid = paid_nocost = 0
    exact = близко = далеко = 0
    worst = []
    for u in data:
        progs = u.get("programs") or []
        total += len(progs)
        ind = u.get("indicators") or {}
        if not progs:
            no_prog.append((u["shortName"], ind.get("Уровни образования")))
        try:
            decl = int(ind.get("Направлений подготовки"))
        except (TypeError, ValueError):
            decl = None
        if decl is not None:
            if decl == len(progs):
                exact += 1
            elif abs(decl - len(progs)) <= 5:
                близко += 1
            else:
                далеко += 1
                worst.append((decl - len(progs), decl, len(progs), u["shortName"][:45]))
        for p in progs:
            levels[p["level"]] += 1
            okso.add(p["okso"])
            if p["placeType"] == "Платные места":
                paid += 1
                if not p.get("cost"):
                    paid_nocost += 1

    print(f"\nЗаписей программ: {total}, уникальных ОКСО: {len(okso)}")
    print("Уровни:", dict(levels))
    print("Уровней «Ординатура»/«Ассистентура-стажировка» в программах:",
          levels.get("Ординатура", 0), "/", levels.get("Ассистентура-стажировка", 0),
          "(систематически не выгружаются)")
    print(f"Платных: {paid}, без стоимости: {paid_nocost} ({100 * paid_nocost / max(1, paid):.1f}%)")
    print(f"Счётчик «Направлений подготовки»: совпал у {exact}, ±5 у {близко}, "
          f"расходится сильнее у {далеко}")
    for w in sorted(worst, reverse=True)[:5]:
        print(f"  заявлено {w[1]}, в списке {w[2]} | {w[3]}")
    print(f"Вузов без программ: {len(no_prog)} (все — ординатура: "
          f"{all('Ординатура' in (lv or '') for _, lv in no_prog)})")

    if csv_path:
        print("\n=== Сверка со старым CSV ===")
        old = {}
        for r in csv.DictReader(open(csv_path, encoding="utf-8-sig")):
            p = (r.get("programs") or "").strip()
            n = None
            if p:
                try:
                    n = len(json.loads(p))
                except json.JSONDecodeError:
                    n = -1  # обрезанная строка
            old[r["id"]] = n
        same = grew = shrank = 0
        fixed = []
        for u in data:
            n_new = len(u.get("programs") or [])
            n_old = old.get(u["id"])
            if n_old is None:
                continue
            if n_old == -1:
                fixed.append(n_new)
            elif n_new == n_old:
                same += 1
            elif n_new > n_old:
                grew += 1
            else:
                shrank += 1
        print(f"Неповреждённые в CSV: совпало {same}, выросло {grew}, потеряло {shrank}")
        if fixed:
            print(f"Бывшие обрезанные ({len(fixed)}): записей теперь "
                  f"от {min(fixed)} до {max(fixed)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
