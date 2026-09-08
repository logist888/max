# -*- coding: utf-8 -*-
"""Инвентарь индексируемых страниц для этапа 2 (Programmatic SEO).

Считает из JSON-выгрузки все количества, на которых стоят пороги
в seo-platform/02-pseo.md.
Запуск: python3 seo-platform/inventory.py <файл.json>
"""
import collections
import json
import re
import sys


def norm_city(c):
    return re.sub(r"^(г\.|город|пос\.|п\.|с\.|пгт\.?|рп\.?|ст-ца|дер\.|д\.)\s*",
                  "", c, flags=re.I).strip().lower()


def main(path):
    data = json.loads(open(path, encoding="utf-8-sig").read())
    rf = [u for u in data if "иностранного" not in (u["region"] or "")]
    print(f"Организаций РФ: {len(rf)} (зарубежных филиалов вне инвентаря: {len(data) - len(rf)})")
    regions = {u["region"] for u in rf}
    cities = {norm_city(u["city"]) for u in rf}

    dc = collections.defaultdict(set)                    # направление × город → вузы
    dr = collections.defaultdict(lambda: (set(), set())) # направление × регион → (вузы, города)
    dirs = set()
    ugs = set()
    for u in rf:
        c, r = norm_city(u["city"]), u["region"]
        for p in (u.get("programs") or []):
            dirs.add(p["okso"])
            m = re.match(r"^\d+\.(\d{2})\.", p["okso"])
            if m:
                ugs.add(m.group(1))
            dc[(p["okso"], c)].add(u["id"])
            k = dr[(p["okso"], r)]
            k[0].add(u["id"])
            k[1].add(c)

    combo_city = sum(1 for s in dc.values() if len(s) >= 2)
    combo_city_all = len(dc)
    combo_reg = sum(1 for unis, cits in dr.values() if len(unis) >= 2 and len(cits) >= 2)
    combo_reg_canon = sum(1 for unis, cits in dr.values() if len(unis) >= 2 and len(cits) == 1)

    mil = collections.Counter(norm_city(u["city"]) for u in rf if u.get("militaryDept"))
    dorm = collections.Counter(norm_city(u["city"]) for u in rf if u.get("dormitory"))
    cost = collections.Counter(
        norm_city(u["city"]) for u in rf
        if any(p["placeType"] == "Платные места" and p.get("cost")
               for p in (u.get("programs") or [])))

    print(f"Регионы: {len(regions)}, города: {len(cities)}, направления: {len(dirs)}, УГСН: {len(ugs)}")
    print(f"Направление × город: всего {combo_city_all}, индексируемых (≥2 вуза): {combo_city}")
    print(f"Направление × регион: индексируемых (≥2 вуза, ≥2 города): {combo_reg}, "
          f"canonical на город (один город): {combo_reg_canon}")
    print(f"Кураторские кандидаты: военная кафедра ≥3 вузов — {sum(1 for v in mil.values() if v >= 3)} городов, "
          f"общежитие ≥5 — {sum(1 for v in dorm.values() if v >= 5)}, "
          f"стоимость ≥5 — {sum(1 for v in cost.values() if v >= 5)}")
    total = len(rf) + len(regions) + len(cities) + len(dirs) + len(ugs) + combo_city + combo_reg
    print(f"Канонический инвентарь без кураторского и редакционного слоёв: {total}")


if __name__ == "__main__":
    main(sys.argv[1])
