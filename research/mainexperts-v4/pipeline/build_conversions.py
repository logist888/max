#!/usr/bin/env python3
"""Build reproducible route, CTA localization and intent binding registries."""

import csv
from pathlib import Path

CONFIG = Path(__file__).resolve().parent / "config"
COMMERCIAL_INTENTS = ("I09", "I10", "I11")
BASE_INTENTS = tuple(f"I{i:02d}" for i in range(1, 15))
PARTNER_PAYMENTS = {
    "R08": "PARTNER_ONCE",
    "R09": "PARTNER_ONCE",
    "R12": "PARTNER_ONCE",
    "R13": "PARTNER_ONCE",
}
OFFICIAL_PAYMENTS = {
    "P10": "EXTERNAL_OFFICIAL_POSSIBLE",
    "P11": "EXTERNAL_OFFICIAL_POSSIBLE",
    "P12": "EXTERNAL_PROVIDER_POSSIBLE",
    "P13": "EXTERNAL_OFFICIAL_POSSIBLE",
    "P16": "EXTERNAL_OFFICIAL_POSSIBLE",
    "P26": "EXTERNAL_OFFICIAL_POSSIBLE",
}


def rows(name):
    with (CONFIG / f"{name}.tsv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def save(name, records):
    with (CONFIG / f"{name}.tsv").open("w", encoding="utf-8", newline="") as f:
        out = csv.DictWriter(f, records[0], delimiter="\t")
        out.writeheader()
        out.writerows(records)


def main():
    services = {r["SERVICE_ID"]: r for r in rows("services")}
    products = {r["PRODUCT_ID"]: r for r in rows("products")}
    phrases = {r["KEY"]: r for r in rows("cta_phrases")}
    languages = list(next(iter(phrases.values())))[1:]
    elements = {r["ELEMENT_ID"] for r in rows("elements")}
    conversions = []
    localizations = []
    bind = []

    def add(service, rule, flavor, primary, secondary, element, trigger, action, target,
            paid_value, payment, fulfilment, location, event, kpi, intent, product_id=""):
        if element not in elements:
            raise ValueError(f"Unknown element {element}")
        code = service["SERVICE_ID"]
        route_id = f"C-{code}-{flavor}"
        conversions.append({
            "CONVERSION_ID": route_id,
            "SERVICE_ID": code,
            "PRODUCT_ID": product_id,
            "ROUTE_KIND": flavor,
            "INTENT_ID": intent,
            "PAGE_TYPE": rule["PAGE_TYPE"],
            "PAGE_URL_PATTERN": "/{locale}/{destination}/" + rule["SLUG"] + "/",
            "ELEMENT_ID": element,
            "CTA_PRIMARY": phrases[primary]["ru"],
            "CTA_SECONDARY": phrases[secondary]["ru"] if secondary else "",
            "CTA_TRIGGER": trigger,
            "CTA_TARGET": target,
            "CTA_PLACEMENT": location,
            "TARGET_ACTION": action,
            "INPUTS": rule["INPUTS"],
            "FREE_VALUE": rule["FREE_VALUE"],
            "PAID_VALUE": paid_value,
            "PAYMENT_TYPE": payment,
            "FULFILMENT": fulfilment,
            "EVENT": event,
            "KPI": kpi,
            "TEST_METHOD": rule["INJECTION_TEST"],
        })
        for lang in languages:
            localizations.append({
                "CONVERSION_ID": route_id,
                "LANGUAGE": lang,
                "CTA_PRIMARY": phrases[primary][lang],
                "CTA_SECONDARY": phrases[secondary][lang] if secondary else "",
                "CTA_PRIMARY_RU": phrases[primary]["ru"],
                "CTA_SECONDARY_RU": phrases[secondary]["ru"] if secondary else "",
            })

    for rule in rows("conversion_rules"):
        code = rule["SERVICE_ID"]
        service = services[code]
        product_id = service["PRODUCT_ID"]
        fallback = rule["O_ACTION"] or "source"
        add(service, rule, "F", rule["FREE_ACTION"], fallback, rule["FREE_ELEMENT"],
            "Посетитель находит ответ по исходной задаче; нет условия регистрации",
            "Открыть результат или заполнить поля для бесплатного расчёта",
            rule["FREE_TARGET"], "", "NONE", "Результат на странице либо в официальном источнике",
            "Рядом с исходным ответом", "free_result_rendered",
            "Сессии с полезным бесплатным результатом / релевантные входные сессии", "DEFAULT")

        has_official = bool(rule["O_ACTION"])
        if has_official:
            add(service, rule, "O", rule["O_ACTION"], rule["FREE_ACTION"], "E03",
                "Официальный получатель установлен и ссылка прошла проверку",
                "Открыть внешний процесс с указанием организации",
                rule["O_TARGET"], "", OFFICIAL_PAYMENTS.get(code, "NONE"),
                "Итог выдаёт официальный оператор", "В ответе и рядом с решением",
                "official_handoff_clicked", "Корректные официальные переходы / показы ссылки", "I12")

        direct = bool(product_id and service["PAYMENT_TYPE"] != "ME_INCLUDED" and code != "P13")
        if product_id:
            product = products[product_id]
            owner = services[product["SERVICE_ID"]]
            pay_type = PARTNER_PAYMENTS.get(product_id, owner["PAYMENT_TYPE"])
            partner = product_id in PARTNER_PAYMENTS
            paid_cta = {"P19": "career_paid", "P21": "expert_paid"}.get(code, product_id)
            delivered = service["PAID_VALUE"] if direct else owner["PAID_VALUE"]
            fulfilment = service["FULFILMENT"] if direct else owner["FULFILMENT"]
            safety = (
                " и поставщик, доступность и полномочия проверены для рынка"
                if partner else " и объём и срок подтверждены, а услуга включена для этого маршрута"
            )
            target = f"partner-checkout/{product_id.lower()}" if partner else f"checkout/{product_id.lower()}"
            conversion_measure = (
                "Завершённые подтверждённые заказы партнёра / клики по партнёру"
                if partner else "Принятые оплаченные заказы / входы в оформление"
            )
            add(service, rule, "A", paid_cta, fallback, "E20", rule["NEED_TRIGGER"] + safety,
                "Выбрать объём и открыть условия заказа",
                f"offer/{product_id.lower()}", delivered, pay_type, fulfilment,
                "После бесплатного результата", "qualified_offer_opened",
                conversion_measure, "I05", product_id)
            if direct:
                add(service, rule, "C", paid_cta, "sample", "E20",
                    "Пользователь прямо ищет специалиста, цену или заказ для этой услуги" + safety,
                    "Уточнить объём, проверить полную цену и приступить к оплате",
                    target, delivered, pay_type, fulfilment, "На коммерческой посадочной",
                    "partner_handoff_clicked" if partner else "checkout_started",
                    conversion_measure, "I11", product_id)

        for intent in BASE_INTENTS:
            if intent == "I12" and has_official:
                flavor = "O"
            elif intent in COMMERCIAL_INTENTS and code in {"P10", "P13"} and has_official:
                flavor = "O"
            elif intent in COMMERCIAL_INTENTS and direct:
                flavor = "C"
            else:
                flavor = "F"
            after = f"C-{code}-A" if product_id else ""
            bind.append({
                "SERVICE_ID": code,
                "INTENT_ID": intent,
                "CONVERSION_ID": f"C-{code}-{flavor}",
                "FALLBACK_CONVERSION_ID": f"C-{code}-F",
                "POST_RESULT_CONVERSION_ID": after,
                "ACTIVATION_RULE": (
                    "Прямой заказ — только для явно совпадающего товара, языка и поддерживаемого маршрута"
                    if flavor == "C" else
                    "Ошибка или неизвестный поставщик — вернуть ответ и ссылку для уточнения"
                    if flavor == "O" else
                    "Первым отдаётся обещанный бесплатный результат"
                ),
            })

    known = {r["CONVERSION_ID"] for r in conversions}
    assert len(known) == len(conversions)
    assert len(bind) == len(BASE_INTENTS) * len(services)
    assert all(r["CONVERSION_ID"] in known and (
        not r["POST_RESULT_CONVERSION_ID"] or r["POST_RESULT_CONVERSION_ID"] in known
    ) for r in bind)
    assert len(localizations) == len(conversions) * len(languages)
    save("conversions", conversions)
    save("cta_localizations", localizations)
    save("conversion_intents", bind)
    print(f"{len(conversions)} flows, {len(localizations)} localizations, {len(bind)} intent bindings")


if __name__ == "__main__":
    main()
