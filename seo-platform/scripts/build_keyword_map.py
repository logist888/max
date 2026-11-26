#!/usr/bin/env python3
"""Матрица распределения семантического ядра v2 → SEO/GEO-архитектура сайта.

Вход: seo/semcore-v2-source.xlsx (ядро Mainexperts v2, уже кластеризованное:
пиллары, интент, сезонность, сиды, asset; листы Core/Noise/Off-scope).
Выход:
- seo/keyword-map.csv — по каждой фразе: сид, целевой URL/тип, статус, приоритет, причина.
- seo/semcore-v2.csv  — нормализованная плоская копия листа Core (воспроизводимость).
- seo/audit.md        — статистика, распределение по кластерам, RICE-бэклог.

Диспозиция — на уровне сид-кластера (файл уже сгруппировал фразы по сидам). Привязана к
проверенной границе данных: где данных сайта нет (СПО, предметы ЕГЭ, спрос) — статус
«Gated/нужны данные» или «контент без рейтинга», а не выдуманная страница (закон проекта).

Запуск: python3 scripts/build_keyword_map.py
"""
import csv
from pathlib import Path
from collections import defaultdict
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "seo" / "semcore-v2-source.xlsx"
OUT = ROOT / "seo"

# Диспозиция по сид-кластеру: (статус, целевой URL/тип, приоритет, причина).
# Статусы из ТЗ: существующая/расширить/новая посадочная/контент-хаб/подборка/gated/не использовать.
DISP = {
    # --- P0: on-data профессии (данные есть: граф 436 + зарплаты Росстат) ---
    "e03_vysokooplachivaemye": ("Создать новую посадочную (рейтинг)", "/professii-vysokooplachivaemye/", "P0", "Рейтинг по зарплатам Росстата окт-2025 — данные есть"),
    "e01_professii_spisok":    ("Расширить существующую", "/professiya/", "P0", "Каталог 436 профессий — данные есть"),
    "b03_kem_mozhno_stat":     ("Расширить существующую", "/professiya/", "P0", "«Кем можно стать» = список профессий → каталог"),
    "b06_kem_pojti_rabotat":   ("Расширить существующую", "/professiya/", "P0", "«Кем пойти работать» = список профессий → каталог"),
    # --- P1: контент-хабы воронки → /test/ (North Star) ---
    "b01_kakuyu_professiyu_vybrat":  ("Создать новый контент-хаб", "/kak-vybrat-professiyu/", "P1", "Инфо-хаб выбора профессии → /test/"),
    "b02_kak_vybrat_professiyu":     ("Создать новый контент-хаб", "/kak-vybrat-professiyu/", "P1", "Инфо-хаб → /test/"),
    "b04_na_kogo_pojti_uchitsya":    ("Создать новый контент-хаб", "/kak-vybrat-professiyu/", "P1", "ВЧ-инфо → хаб выбора + каталоги + /test/"),
    "b05_kakaya_professiya_podhodit":("Создать новый контент-хаб", "/kak-vybrat-professiyu/", "P1", "Подбор профессии → /test/"),
    "b07_ne_znayu_kem_stat":         ("Создать новый контент-хаб", "/kak-vybrat-professiyu/", "P1", "Боль «не знаю кем стать» → /test/"),
    "p01_proforientaciya":       ("Создать новый контент-хаб", "/proforientaciya/", "P1", "Хаб профориентации → /test/"),
    "p02_prof_dlya_podrostkov":  ("Расширить (раздел хаба)", "/proforientaciya/", "P1", "Срез «для подростков»"),
    "p03_prof_dlya_shkolnikov":  ("Расширить (раздел хаба)", "/proforientaciya/", "P1", "Срез «для школьников»"),
    "p04_prof_online":           ("Расширить (раздел хаба)", "/proforientaciya/", "P1", "«Онлайн» → /test/"),
    "p05_prof_9_klass":          ("Расширить (раздел хаба)", "/proforientaciya/", "P1", "Профориентация 9 класс (контент, не листинг СПО)"),
    "p06_projti_proforientaciyu":("Использовать существующую", "/test/", "P1", "Транзакционный «пройти» → квиз"),
    "p07_centr_proforientacii":  ("Расширить (раздел хаба)", "/proforientaciya/", "P1", "«Центр профориентации» → хаб/онлайн"),
    "p08_proforientaciya_2026":  ("Расширить (раздел хаба)", "/proforientaciya/", "P1", "Year-stamp → хаб"),
    "d01_test_na_proforientaciyu":("Создать новый контент-хаб", "/testy-na-proforientaciyu/", "P1", "Хаб о тестах → /test/ (SERP: формат-статья достижим)"),
    "d02_test_besplatno":        ("Расширить (раздел хаба)", "/testy-na-proforientaciyu/", "P1", "«Бесплатно» → хаб/квиз"),
    "d03_test_online":           ("Расширить (раздел хаба)", "/testy-na-proforientaciyu/", "P1", "«Онлайн» → квиз"),
    "d04_projti_test":           ("Использовать существующую", "/test/", "P1", "Транзакционный «пройти тест» → квиз"),
    "d05_test_na_professiyu":    ("Расширить (раздел хаба)", "/testy-na-proforientaciyu/", "P1", "«Тест на профессию» → хаб → /test/"),
    "d06_test_na_vybor_professii":("Использовать существующую", "/test/", "P1", "Прямой интент квиза"),
    "d07_test_gollanda":         ("Создать статью в хабе", "/testy-na-proforientaciyu/test-gollanda/", "P1", "Именованная методика (RIASEC — рабочее название)"),
    "d08_test_klimova":          ("Создать статью в хабе", "/testy-na-proforientaciyu/test-klimova/", "P1", "Именованная методика Климова"),
    "d09_ddo_klimova":           ("Создать статью в хабе", "/testy-na-proforientaciyu/test-klimova/", "P1", "ДДО Климова (та же методика)"),
    "a01_rebenok_ne_znaet":      ("Создать новый контент-хаб", "/roditelyam/", "P1", "Родителям; SERP: main-experts 0/10 — greenfield"),
    "a02_kak_pomoch_podrostku":  ("Расширить (раздел хаба)", "/roditelyam/", "P1", "Родителям подростка"),
    "a04_prof_dlya_rebenka":     ("Расширить (раздел хаба)", "/roditelyam/", "P1", "Профессии для ребёнка (контент)"),
    # --- E без данных о спросе: контент без числового рейтинга ---
    "e02_vostrebovannye":        ("Контент-хаб без рейтинга", "/professiya/ (раздел)", "P1", "Нет данных о спросе (hh заблокирован) — не ранжируем"),
    "e04_professii_buduschego":  ("Контент-хаб без рейтинга", "/professiya/ (раздел)", "P1", "Нет данных прогноза — контент без рейтинга"),
    # --- P2: on-data после 11 / гендер (в рамках направлений/вузов) ---
    "c02_kuda_postupat_posle_11":("Создать новый контент-хаб", "/kuda-postupat-posle-11-klassa/", "P2", "После 11 → вузы/направления (данные есть)"),
    "c04_professii_posle_11":    ("Расширить существующую", "/professiya/ + хаб-11", "P2", "Профессии после 11 → каталог/направления"),
    "c08_kuda_postupat_devushke":("Контент/фильтр (не дубль)", "/kuda-postupat-posle-11-klassa/#devushke", "P2", "Гендер-срез после 11"),
    "c09_kuda_postupat_parnyu":  ("Контент/фильтр (не дубль)", "/kuda-postupat-posle-11-klassa/#parnyu", "P2", "Гендер-срез после 11"),
    # --- P3 GATED: нет данных СПО (после 9 / колледжи) ---
    "c01_kuda_postupat_posle_9": ("Gated — нужны данные", "—", "P3", "Нет реестра СПО (после 9)"),
    "c03_professii_posle_9":     ("Gated — нужны данные", "—", "P3", "Нет данных СПО/уровня после 9"),
    "c05_postupit_v_kolledzh":   ("Gated — нужны данные", "—", "P3", "Нет реестра колледжей (СПО)"),
    "c06_specialnosti_posle_9":  ("Gated — нужны данные", "—", "P3", "Нет реестра СПО (специальности после 9)"),
    "c07_kem_stat_posle_9":      ("Gated — нужны данные", "—", "P3", "Нет данных СПО"),
    # --- P3-B ГОТОВО: ЕГЭ-предметы → направления (перечень Минобрнауки № 820) ---
    "c10_s_obschestvoznaniem":   ("Создана посадочная", "/kuda-postupat-s-obshchestvoznaniem/", "P3", "Перечень Минобрнауки → направления (готово)"),
    "c11_s_istoriej":            ("Создана посадочная", "/kuda-postupat-s-istoriej/", "P3", "Перечень Минобрнауки → направления (готово)"),
    "c12_s_biologiej":           ("Создана посадочная", "/kuda-postupat-s-biologiej/", "P3", "Перечень Минобрнауки → направления (готово)"),
    "c13_s_informatikoj":        ("Создана посадочная", "/kuda-postupat-s-informatikoj/", "P3", "Перечень Минобрнауки → направления (готово)"),
    "c14_s_himiej":              ("Создана посадочная", "/kuda-postupat-s-himiej/", "P3", "Перечень Минобрнауки → направления (готово)"),
    "c15_s_fizikoj":             ("Создана посадочная", "/kuda-postupat-s-fizikoj/", "P3", "Перечень Минобрнауки → направления (готово)"),
    "c16_s_geografiej":          ("Создана посадочная", "/kuda-postupat-s-geografiej/", "P3", "Перечень Минобрнауки → направления (готово)"),
    # --- P3 GATED: гео-колледжи (нет СПО) ---
    "g01_kolledzhi_krasnoyarsk": ("Gated — нужны данные", "—", "P3", "Нет реестра СПО (колледжи города)"),
    "g02_kolledzhi_perm":        ("Gated — нужны данные", "—", "P3", "Нет реестра СПО (колледжи города)"),
    "g03_kolledzhi_voronezh":    ("Gated — нужны данные", "—", "P3", "Нет реестра СПО (колледжи города)"),
    "g04_kolledzhi_tyumen":      ("Gated — нужны данные", "—", "P3", "Нет реестра СПО (колледжи города)"),
    "g05_kolledzhi_irkutsk":     ("Gated — нужны данные", "—", "P3", "Нет реестра СПО (колледжи города)"),
}

# Фолбэк по первой букве сида, если сид не в таблице.
FALLBACK = {
    "e": ("Расширить существующую", "/professiya/", "P1", "Профессии — каталог/контент"),
    "b": ("Создать новый контент-хаб", "/kak-vybrat-professiyu/", "P1", "Выбор профессии → /test/"),
    "p": ("Создать новый контент-хаб", "/proforientaciya/", "P1", "Профориентация → /test/"),
    "d": ("Создать новый контент-хаб", "/testy-na-proforientaciyu/", "P1", "Тесты → /test/"),
    "a": ("Создать новый контент-хаб", "/roditelyam/", "P1", "Родителям"),
    "c": ("Gated — нужны данные", "—", "P3", "Пиллар C: вероятно СПО/ЕГЭ — нет данных"),
    "g": ("Gated — нужны данные", "—", "P3", "Гео-колледжи — нет реестра СПО"),
}

IMPACT = {"P0": 3.0, "P1": 2.0, "P2": 1.5, "P3": 1.0}


def disp_for(seed):
    if seed in DISP:
        return DISP[seed]
    return FALLBACK.get(seed[:1], ("Не классифицировано", "—", "P3", "Нет правила"))


def num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def main():
    wb = load_workbook(SRC, read_only=True, data_only=True)

    # --- Core ---
    ws = wb["Core"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(h) for h in rows[0]]
    ix = {name: hdr.index(name) for name in hdr}
    iPhrase = ix["Фраза"]; iShow = ix["Показы (broad, снимок 30 дн)"]; iType = ix["Тип"]
    iPil = ix["Пиллар"]; iInt = ix["Интент"]; iAsset = ix["Asset"]; iSid = ix["Сиды"]
    core = rows[1:]

    # нормализованная копия
    with open(OUT / "semcore-v2.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(hdr)
        for r in core:
            w.writerow(["" if v is None else v for v in r])

    # keyword-map + агрегация по сидам
    seed_agg = defaultdict(lambda: [0, 0])  # phrases, shows
    seed_meta = {}
    map_rows = []
    for r in core:
        phrase = r[iPhrase]
        if phrase is None:
            continue
        shows = num(r[iShow])
        seed = (str(r[iSid]).split(";")[0]) if r[iSid] else "—"
        status, target, prio, reason = disp_for(seed)
        map_rows.append([phrase, shows, r[iPil], r[iInt], r[iType], seed, r[iAsset], status, prio, target, reason])
        seed_agg[seed][0] += 1
        seed_agg[seed][1] += shows
        seed_meta[seed] = (status, target, prio, reason, r[iPil])

    # Noise + Off-scope → «Не использовать»
    def add_excluded(sheet, reason_col, cat_label):
        ws2 = wb[sheet]
        rr = list(ws2.iter_rows(values_only=True))
        h2 = [str(x) for x in rr[0]]
        ip = h2.index("Фраза"); ish = h2.index("Показы")
        ire = h2.index(reason_col) if reason_col in h2 else None
        n = 0
        for row in rr[1:]:
            if row[ip] is None:
                continue
            reason = (str(row[ire]) if ire is not None and row[ire] else cat_label)
            map_rows.append([row[ip], num(row[ish]), "—", "—", "—", "—", "—",
                             "Не использовать", "—", "—", f"{cat_label}: {reason}"])
            n += 1
        return n

    n_noise = add_excluded("Noise", "Причина", "noise")
    n_off = add_excluded("Off-scope", "Категория", "off-scope")
    wb.close()

    with open(OUT / "keyword-map.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Фраза", "Показы", "Пиллар", "Интент", "Тип", "Сид", "Asset",
                    "Статус", "Приоритет", "ЦелевойURL", "Причина"])
        w.writerows(map_rows)

    # --- RICE-бэклог по сидам ---
    backlog = []
    for seed, (nph, shows) in seed_agg.items():
        status, target, prio, reason, pil = seed_meta[seed]
        gated = status.startswith("Gated")
        conf = 0.5 if (gated or "без рейтинга" in status) else 1.0
        effort = {"Создать новую посадочную (рейтинг)": 2, "Создать новый контент-хаб": 3,
                  "Расширить существующую": 1, "Использовать существующую": 0.5}.get(status, 2)
        rice = round(shows * IMPACT.get(prio, 1.0) * conf / effort)
        backlog.append((rice, seed, nph, shows, prio, status, target, reason))
    backlog.sort(reverse=True)

    # --- сводки для audit.md ---
    by_status = defaultdict(lambda: [0, 0])
    by_prio = defaultdict(lambda: [0, 0])
    for r in map_rows:
        by_status[r[7]][0] += 1; by_status[r[7]][1] += num(r[1])
        by_prio[r[8]][0] += 1; by_prio[r[8]][1] += num(r[1])

    total_core = len(core)
    lines = []
    lines.append("# Аудит семантического ядра v2 → SEO/GEO-архитектура\n")
    lines.append(f"Источник: `seo/semcore-v2-source.xlsx` (Mainexperts v2, сбор 14.07.2026). "
                 f"Матрица по фразам: `seo/keyword-map.csv`.\n")
    lines.append("## 1. Общая статистика\n")
    lines.append(f"- Core-фраз: **{total_core}**; исключено листами ядра: Noise **{n_noise}**, Off-scope **{n_off}**.")
    lines.append(f"- Сид-кластеров: **{len(seed_agg)}**.")
    lines.append("- Распределение по приоритету (фраз / показов):")
    for p in ["P0", "P1", "P2", "P3", "—"]:
        if p in by_prio:
            lines.append(f"  - {p}: {by_prio[p][0]} / {by_prio[p][1]:,}")
    lines.append("- Распределение по статусу (фраз / показов):")
    for st, (n, s) in sorted(by_status.items(), key=lambda x: -x[1][1]):
        lines.append(f"  - {st}: {n} / {s:,}")
    lines.append("\n## 2. Бэклог по RICE (сид-кластеры, по убыванию)\n")
    lines.append("RICE = Показы × Impact(приоритет) × Confidence(данные) / Effort. Confidence 0.5 для gated/без-рейтинга.\n")
    lines.append("| RICE | Сид | Фраз | Показы | Приоритет | Статус | Цель | Причина |")
    lines.append("|---:|---|---:|---:|---|---|---|---|")
    for rice, seed, nph, shows, prio, status, target, reason in backlog:
        lines.append(f"| {rice:,} | {seed} | {nph} | {shows:,} | {prio} | {status} | {target} | {reason} |")
    lines.append("\n## 3. Честная граница (правило «не выдумывать»)\n")
    lines.append("- **Gated (P3)**: пиллар C (колледжи/СПО, после 9), ЕГЭ-связки, гео-колледжи — "
                 "нет данных в БД (только вузы). Не строим страницы без источника; при появлении "
                 "реестра СПО и предметов ЕГЭ разблокируется (data-acquisition владельца).")
    lines.append("- **Без числового рейтинга**: «востребованные / профессии будущего» — нет данных о "
                 "спросе (hh заблокирован ToS) — только контент, без выдуманного ранжирования.")
    lines.append("- **On-data (P0)**: высокооплачиваемые профессии (зарплаты Росстат окт-2025) и каталог "
                 "профессий (436) — реальные данные, строим сразу.")
    (OUT / "audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"seo/keyword-map.csv: {len(map_rows)} строк (core {total_core} + noise {n_noise} + off {n_off})")
    print(f"seo/semcore-v2.csv: {total_core} строк; seo/audit.md готов.")
    print("Топ-8 бэклога:")
    for row in backlog[:8]:
        print(f"  RICE {row[0]:>9,} | {row[1]:32} | {row[4]} | {row[5]}")


if __name__ == "__main__":
    main()
