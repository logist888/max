#!/usr/bin/env python3
"""Produce narrowly scoped review suggestions from observed D3 error families."""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


def suggestion(row):
    q = row["QUERY_NORMALIZED"].lower()
    service = row["SERVICE_ID"]
    language = row["LANGUAGE"]
    if service == "P04":
        if re.search(r"\b(bachelor|master|licence)\b|^بكالوريوس", q):
            intent = "I01" if re.search(r"\b(fee|fees|cost|tuition)\b", q) else "I02"
            return "D1", intent, service, "Название, стоимость или поиск программы, а не аудит"
    if service in {"P20", "P21"} and language in {"en", "und"}:
        if re.search(r"\b(how to become|jobs?|salary|how much .* (earn|make))\b", q):
            return "D0", "", "", "Действие или доход поставщика услуги"
        if service == "P21" and re.search(r"^(what is|questions to ask)", q):
            return "D1", "I01", service, "Пользователь узнаёт о роли или готовится к разговору"
        if service == "P20" and q == "sat practice test book":
            return "D2", "I07", "", "Поиск учебного материала, требуется отдельный товарный маршрут"
        if service == "P20" and q.startswith("border patrol agent "):
            return "D0", "", "", "Профессиональный входной тест вне текущего маршрута академической подготовки"
        if service == "P20" and re.search(r"\b(schoolhouse|princeton|college board)\b", q):
            if not re.search(r"\b(price|cost|buy|order|book)\b", q):
                return "D1", "I12", service, "Запрос конкретного поставщика"
    if service == "P20" and language == "ru":
        if re.search(r"(как (начать|стать|быть|работать|заниматься|устроиться)|"
                     r"с чего начать|зарплата|зарабатыва|работа(ть)? репетитором|"
                     r"устроиться репетитором|должен делать|какие обязанности|"
                     r"обязанности|обучение (на репетитора|репетиторству)|"
                     r"учеников для репетитор|учеников репетитору|курс для репетитор|"
                     r"платформы для репетитор|резюме репетитор|"
                     r"сколько (получа[ею]т|платят репетиторам)|"
                     r"что нужно (сдавать|чтобы стать)|курсы репетиторов|"
                     r"сайты для репетиторов|форум репетиторов|ресурсы для репетитора)", q):
            return "D0", "", "", "Сторона поставщика, профессиональная роль или поиск учеников"
        if re.search(r"(100\s*[бb]([аa]л+ь?ный)? репетитор|сто[бb]а[лl]+ь?н(ый|ик)|"
                     r"авито|профи ру|profi ru|skillspace ru|умскул|фоксфорд|"
                     r"яндекс репетитор|скайсмарт|эрик ковалев)", q):
            if not re.search(r"\b(цена|цены|стоимость|заказать|оплатить|купить)\b", q):
                return "D1", "I12", service, "Брендовый поиск поставщика, цены или заказа в формулировке нет"
        if re.search(r"^(кому нужен|кто нуждается|нужен ли|как выбрать|как провер(ить|ять))", q):
            return "D1", "I01", service, "Инструкция выбора или оценка необходимости"
    if service == "P01" and q.startswith("для какой возрастной категории"):
        return "D1", "I01", service, "Информация о применимости профориентации"
    if service == "P23":
        if re.search(r"\b(sports coaching personal statement|college essay tips)\b", q):
            return "D1", "I01", service, "Тема образца или материалы для самостоятельной подготовки"
        if re.search(r"\bpersonal statement writer service\b", q):
            return "D3", "I09", "", "Спрос на подмену авторства, продукт проверки требует авторский черновик"
        if q == "personal statement service" and "ucas.com/" in row["TARGET_URL"]:
            return "D2", "I07", service, "Неоднозначный запрос, официальная цель предоставляет инструмент"
        if re.search(r"\b(tutor|tutors|tutoring)\b", q):
            return "D3", "I09", "P20", "Наставничество по написанию как отдельный результат"
    if service == "P11":
        if q == "ontario college application service":
            return "D1", "I12", service, "Конкретный официальный интерфейс подачи"
        if q == "university application consultant":
            return "D3", "I09", "P21", "Поиск консультанта без обещания проверки комплекта"
    if service == "P13" and q == "wes evaluation services":
        return "D1", "I12", service, "Конкретный внешний оценщик"
    if service == "P18" and re.search(r"\bsans frais d[ '’]agence\b", q):
        return "D1", "I02", service, "Явное требование отсутствия агентской комиссии"
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    counts = Counter()
    with args.candidates.open(encoding="utf-8", newline="") as inp, args.output.open(
        "w", encoding="utf-8", newline=""
    ) as out:
        reader = csv.DictReader(inp)
        fields = ["QUERY_ID", "QUERY_RAW", "SERVICE_FROM", "SERVICE_TO", "INTENT_TO", "EVIDENCE_TO", "REASON"]
        writer = csv.DictWriter(out, fields)
        writer.writeheader()
        for row in reader:
            proposal = suggestion(row)
            if not proposal:
                continue
            level, intent, service, reason = proposal
            counts[(row["SERVICE_ID"], level)] += 1
            writer.writerow({
                "QUERY_ID": row["QUERY_ID"], "QUERY_RAW": row["QUERY_RAW"],
                "SERVICE_FROM": row["SERVICE_ID"], "SERVICE_TO": service, "INTENT_TO": intent,
                "EVIDENCE_TO": level, "REASON": reason,
            })
    for (service, level), count in sorted(counts.items()):
        print(f"{service} → {level}: {count}")


if __name__ == "__main__":
    main()
