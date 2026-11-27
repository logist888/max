# -*- coding: utf-8 -*-
"""Коммерческий слой v4.0 поверх карты по онтологии v2.0.

Источник: комплект «MainExperts v4.0. Коммерческий спрос и образовательный путь» от 26.11.2026
(vault/10-sources/2026-11-26-mainexperts-v4/, данные — docs/cjm-ontology/v4/).
Дословно берётся: услуги P01–P26, уровни доказательства D0–D3, счётчики запросов, сценарии конверсии C-Pxx-F/A/C/O
(кнопка, элемент, событие), получатель платежа, внешние платежи, состояния J01–J09, 14 региональных маршрутов.
Выбрано здесь: колонка стикера (группа 0 ветки Q услуги), дорожка и цвет узла предложения, сжатие текстов.
"""
import csv
import os

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.normpath(os.path.join(HERE, "..", "..", "docs", "cjm-ontology", "v4"))

PAY = {
    "ME_EXPERT_ONCE": "MainExperts, разовая экспертная услуга",
    "ME_ONCE": "MainExperts, разовая услуга",
    "ME_HYBRID_ONCE": "MainExperts, автоматика и эксперт на исключениях",
    "ME_INCLUDED": "входит в бесплатную базу, платно только исключение",
    "ME_SEASON_PASS": "MainExperts, сезонный пропуск",
    "PARTNER_ONCE": "партнёр принимает оплату и отвечает за исполнение",
    "EXTERNAL_OFFICIAL_OR_PARTNER": "официальный оператор или партнёр",
    "NONE": "платного предложения нет",
}
# дорожка узла предложения: у MainExperts цвет дорожки платформы, у партнёра — финансирующей стороны, у официального — органа
NODE_STYLE = {"ME": "L_platform", "PARTNER": "L_funder", "EXTERNAL": "L_authority", "NONE": "L_person"}
KIND_ORDER = {"F": 0, "A": 1, "C": 2, "O": 3}
KIND_NAME = {"F": "бесплатно", "A": "после результата", "C": "прямой заказ", "O": "официальный переход"}
EVENT_NAME = {
    "free_result_rendered": "бесплатный результат показан",
    "qualified_offer_opened": "открыто предложение при триггере",
    "official_handoff_clicked": "переход к официальному источнику",
    "checkout_started": "начато оформление",
    "partner_handoff_clicked": "переход к партнёру",
}
EVIDENCE = {
    "D0": "сигнала в выгрузках нет",
    "D1": "информационный запрос",
    "D2": "запрос инструмента или персонального результата",
    "D3": "коммерческая формулировка",
}


def _tsv(name):
    with open(os.path.join(V4, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def _csv(name):
    with open(os.path.join(V4, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _n(x):
    return "{:,}".format(int(x)).replace(",", " ")


def load():
    svc = {r["SERVICE_ID"]: r for r in _csv("service_summary.csv")}
    conv = {}
    for r in _tsv("conversions.tsv"):
        conv.setdefault(r["SERVICE_ID"], []).append(r)
    for v in conv.values():
        v.sort(key=lambda r: KIND_ORDER[r["ROUTE_KIND"]])
    links = yaml.safe_load(open(os.path.join(V4, "journey-v4-links.yaml"), encoding="utf-8"))
    j4 = yaml.safe_load(open(os.path.join(V4, "journey-v4.yaml"), encoding="utf-8"))
    ext = {}
    pay_by_col = {s["col"]: s["text"].split(" ·")[0] for s in j4["stickies"] if s["row"] == "payment"}
    for s in j4["stickies"]:
        if s["row"] == "external":
            ext[pay_by_col[s["col"]]] = s["text"]
    market = {}
    for r in _csv("country_service.csv"):
        if r["SEARCH_MARKET"] in ("RU", "AE"):
            market.setdefault(r["SERVICE_ID"], {})[r["SEARCH_MARKET"]] = r
    return svc, conv, links, ext, market


def payer_class(pt):
    if pt.startswith("ME_"):
        return "ME"
    if pt == "PARTNER_ONCE":
        return "PARTNER"
    if pt.startswith("EXTERNAL"):
        return "EXTERNAL"
    return "NONE"


def clip(t, n=560):
    t = " ".join(t.split())
    if len(t) <= n:
        return t
    cut = t[:n].rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:.") + "…"


def short_cta(r):
    return "%s «%s»" % (r["ELEMENT_ID"], r["CTA_PRIMARY"])


def apply(doc, colof, nodeof, stages_of_q, branches_with_services=None):
    """Добавляет дорожку, шаги предложений, ряды и стикеры слоя v4 в doc. colof: (ветка, группа) -> колонка."""
    svc, conv, links, ext, market = load()
    ccol = lambda q: colof[(q, 0)]
    by_q = {}
    for sid, r in svc.items():
        by_q.setdefault(r["Q_ID"], []).append(sid)

    # --- дорожка и шаги предложений
    doc["lanes"].append({"id": "L_offer", "label": "Предложение v4: MainExperts, партнёр, официальный переход", "style": 6})
    for q, sids in sorted(by_q.items()):
        sids.sort(key=lambda s: int(s[1:]))
        classes = [payer_class(svc[s]["PAYMENT_TYPE"]) for s in sids]
        main = "ME" if "ME" in classes else ("PARTNER" if "PARTNER" in classes else ("EXTERNAL" if "EXTERNAL" in classes else "NONE"))
        node = {"id": "o_" + q, "shape": "doc", "col": ccol(q), "lane": "L_offer", "style": NODE_STYLE[main],
                "text": "Предложения ветки %s: %s" % (q, ", ".join(sids)), "hypothesis": True}
        doc["flow"]["nodes"].append(node)
        doc["flow"]["edges"].append({"from": nodeof[(q, 0)], "to": "o_" + q, "dash": True, "arrow": True})

    # --- ряды
    rows = doc["rows"]
    rows += [
        {"id": "v4_demand", "label": "v4 · Спрос в поиске: уровень D0–D3, запросы, рынки"},
        {"id": "v4_decision", "label": "v4 · Решение по услуге (стратегия v4)"},
        {"id": "v4_free", "label": "v4 · Бесплатный результат до любой оплаты"},
        {"id": "v4_cta", "label": "v4 · Экран, элемент и текст кнопки по сценариям F · A · C · O"},
        {"id": "v4_trigger", "label": "v4 · Когда предлагать платный результат"},
        {"id": "v4_payer", "label": "v4 · Платный результат, кто принимает деньги, внешний платёж"},
        {"id": "v4_risk", "label": "v4 · Риск и бесплатная альтернатива"},
        {"id": "v4_region", "label": "v4 · Рынок: официальный маршрут и граница платного (14 систем)"},
        {"id": "v4_jstate", "label": "v4 · Состояние маршрута J01–J09 и переходы"},
        {"id": "v4_events", "label": "v4 · Что измеряем на этапе (события)", "type": "goal"},
    ]
    st = doc["stickies"]
    for sid in sorted(svc, key=lambda s: int(s[1:])):
        r = svc[sid]
        c = ccol(r["Q_ID"])
        tail = ""
        mk = market.get(sid, {})
        if mk:
            tail = " Рынки проекта: " + "; ".join("%s %s (%s)" % (m, _n(v["UNIQUE_QUERIES"]), v["EVIDENCE_LEVEL"]) for m, v in sorted(mk.items()))
        else:
            tail = " В России и ОАЭ запросов по услуге нет."
        d3 = int(r["D3"])
        st.append({"row": "v4_demand", "col": c, "kind": "b",
                   "text": clip("%s · %s. Уровень %s (%s): %s запросов в %s рынках; D3 %s, D2 %s, D1 %s.%s" % (
                       sid, r["SERVICE_NAME"], r["EVIDENCE_LEVEL"], EVIDENCE[r["EVIDENCE_LEVEL"]], _n(r["UNIQUE_QUERIES"]), r["MARKETS"],
                       _n(r["D3"]), _n(r["D2"]), _n(r["D1"]), tail))})
        st.append({"row": "v4_decision", "col": c, "kind": "y", "text": clip("%s · %s%s" % (sid, r["ASSESSMENT"], (" Продукт %s." % r["PRODUCT_ID"]) if r["PRODUCT_ID"] else " Продукта нет."))})
        cs = conv.get(sid, [])
        free = next((x for x in cs if x["ROUTE_KIND"] == "F"), None)
        st.append({"row": "v4_free", "col": c, "kind": "g",
                   "text": clip("%s · %s. Самостоятельно: %s" % (sid, free["FREE_VALUE"] if free else "—", r["SELF_SERVICE"]))})
        parts = []
        for x in cs:
            tgt = x["CTA_TARGET"]
            parts.append("%s: %s → %s" % (x["ROUTE_KIND"], short_cta(x), tgt))
        url = free["PAGE_URL_PATTERN"] if free else ""
        st.append({"row": "v4_cta", "col": c, "kind": "y", "text": clip("%s · %s. %s" % (sid, url, ". ".join(parts)))})
        st.append({"row": "v4_trigger", "col": c, "kind": "w", "text": clip("%s · %s" % (sid, r["DELEGATION_TRIGGER"]))})
        paid = r["PAID_VALUE"]
        e = ext.get(sid, "")
        e = "" if (not e or e.startswith("Нет типового")) else " Внешний платёж отдельно: %s." % e.lower()
        st.append({"row": "v4_payer", "col": c, "kind": "w",
                   "text": clip("%s · %s. Платный результат: %s. Исполнение: %s.%s" % (sid, PAY[r["PAYMENT_TYPE"]], paid, r["FULFILMENT"], e))})
        st.append({"row": "v4_risk", "col": c, "kind": "r",
                   "text": clip("%s · Бесплатно уже есть: %s. Риск: %s" % (sid, r["FREE_COMPETITOR"], r["RISK"]))})

    # --- 14 региональных маршрутов
    for g in links["regions"]:
        q = svc[g["service"]]["Q_ID"]
        st.append({"row": "v4_region", "col": ccol(q), "kind": "gr",
                   "text": clip("%s · %s, %s. Маршрут: %s. Официальный источник: %s. Бесплатно: %s Платное: %s" % (
                       g["id"], g["title"], g["state"], g["pathway"], g["provider"], g["free"], g["gate"]))})

    # --- состояния J01–J09
    trans = {}
    for t in links["transitions"]:
        trans.setdefault(t["from"], []).append("%s: %s" % (t["to"], t["condition"].rstrip(".").lower()))
    for s in links["states"]:
        first = s["questions"][0]
        st.append({"row": "v4_jstate", "col": ccol(first), "kind": "w",
                   "text": clip("%s · %s. Классы %s. Результат: %s Развилка: %s Переходы: %s." % (
                       s["id"], s["label"], ", ".join(s["questions"]), s["result"], s["choice"], "; ".join(trans.get(s["id"], ["—"]))), 600)})

    # --- события по этапам: что измеряется, по числу сценариев услуг этапа
    for stg in doc["stages"]:
        qs = stages_of_q[stg["id"]]
        cnt = {}
        n_c = 0
        for sid, r in svc.items():
            if r["Q_ID"] in qs:
                for x in conv.get(sid, []):
                    cnt[x["EVENT"]] = cnt.get(x["EVENT"], 0) + 1
                    if x["ROUTE_KIND"] == "C":
                        n_c += 1
        order = ["free_result_rendered", "qualified_offer_opened", "checkout_started", "partner_handoff_clicked", "official_handoff_clicked"]
        txt = "; ".join("%s ×%d (%s)" % (k, cnt[k], EVENT_NAME[k]) for k in order if k in cnt)
        n_svc = sum(1 for r in svc.values() if r["Q_ID"] in qs)
        st.append({"row": "v4_events", "stage": stg["id"], "kind": "gr",
                   "text": clip("Услуг этапа: %d. Сценариев по событиям: %s. После checkout_started: payment_confirmed, fulfilment_delivered, fulfilment_accepted, order_refunded." % (n_svc, txt or "нет"), 600)})
    return doc
