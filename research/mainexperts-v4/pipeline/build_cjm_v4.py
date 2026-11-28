#!/usr/bin/env python3
"""Rebuild the CJM v4 publication from CJM v3, shared registries and the pinned renderer."""

import argparse
import collections
import copy
import csv
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import sys

import yaml

GENERATOR_COMMIT = "14816a72b5a30579cf46a47084e6b0739cb2a36a"
GENERATOR_URL = f"https://github.com/logist888/max/tree/{GENERATOR_COMMIT}/.claude/skills/cjm-map"
TODAY = "2026-11-26"
PAYMENT = {
    "ME_EXPERT_ONCE": "MainExperts · фиксированная экспертная услуга",
    "ME_HYBRID_ONCE": "MainExperts · фиксированная цена с экспертной проверкой",
    "ME_ONCE": "MainExperts · разовая цифровая покупка",
    "ME_INCLUDED": "MainExperts · входит в пакет, отдельной оплаты нет",
    "ME_SEASON_PASS": "MainExperts · доступ на сезон",
    "PARTNER_ONCE": "Партнёр · платёж исполнителю",
    "EXTERNAL_OFFICIAL_OR_PARTNER": "Внешний официальный сбор или отдельная услуга партнёра",
    "EXTERNAL_OFFICIAL_POSSIBLE": "Возможный сбор в официальном канале",
    "EXTERNAL_PROVIDER_POSSIBLE": "Возможная оплата поставщику",
    "NONE": "Самостоятельный маршрут, покупка не предлагается",
}
ROW_DESCRIPTIONS = {
    "intent": "Поисковые кластеры",
    "free_v4": "Бесплатный результат",
    "interface_v4": "Экран, элемент и CTA",
    "decision_v4": "Когда предложить платный результат",
    "payment_v4": "Получатель платежа и исполнение",
}
LEGEND = [
    {"kind": "ghost", "text": "Проектная гипотеза"},
    {"kind": "b", "text": "Переход или сценарий"},
    {"kind": "g", "text": "Бесплатный результат"},
    {"kind": "gr", "text": "Данные и ограничения"},
]
DETAIL_SUBSETS = {
    "s0": "Цель и ориентация",
    "s1": "Поиск и сравнение",
    "s2": "Осуществимость",
    "s3": "Подготовка и приём",
    "s4": "Обучение и переход",
}
NO_AGGREGATE = "Сводка поисковых данных для услуги отсутствует."
COUNTRY_SUMMARY_COLUMNS = ("Рынок поиска", "Записей", "D1", "D2", "D3", "Языки", "Кластеры")


def read_csv(path):
    if not path.is_file():
        return []
    delimiter = "\t" if path.suffix == ".tsv" else ","
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=delimiter))


def read_yaml(path):
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def write_yaml(path, data):
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")


def as_integer(value):
    return int(float(value or 0))


def formatted(value):
    return f"{value:,}".replace(",", " ")


def levels(value):
    found = re.search(r"D([0-6])", str(value))
    return int(found.group(1)) if found else 0


def collect_evidence(rows, cluster_rows):
    cluster_totals = collections.defaultdict(collections.Counter)
    for row in cluster_rows:
        if row.get("SERVICE_ID") and row.get("CLUSTER_ID"):
            key = (row["SERVICE_ID"], row["SEARCH_MARKET"])
            cluster_totals[key][row["CLUSTER_ID"]] += as_integer(row["UNIQUE_QUERIES"])
    indexed = collections.defaultdict(list)
    for row in rows:
        if row.get("SERVICE_ID"):
            with_clusters = dict(row)
            key = (row["SERVICE_ID"], row["SEARCH_MARKET"])
            with_clusters["CLUSTER_KEYS"] = cluster_totals[key].most_common(6)
            indexed[row["SERVICE_ID"]].append(with_clusters)
    return indexed


def country_summary_rows(evidence):
    return [
        (row["SEARCH_MARKET"], row["UNIQUE_QUERIES"], row["D1_QUERIES"], row["D2_QUERIES"],
         row["D3_QUERIES"], row["LANGUAGES"], ", ".join(key for key, _ in row["CLUSTER_KEYS"][:3]))
        for row in evidence
    ]


def short_evidence(rows):
    if not rows:
        return NO_AGGREGATE
    observed = [r for r in rows if as_integer(r.get("UNIQUE_QUERIES"))]
    if not observed:
        return "В обработанной сводке поисковая поддержка услуги не обнаружена."
    best = max(levels(r.get("EVIDENCE_LEVEL")) for r in observed)
    market_count = len({r["SEARCH_MARKET"] for r in observed if r["SEARCH_MARKET"] != "ZZ-RU"})
    commercial = sum(as_integer(r.get("D3_QUERIES")) for r in rows)
    return f"D{best} максимум · рынков {market_count} · записей с коммерческим намерением {formatted(commercial)}."


def as_note(text, col, row, kind="gr"):
    if len(text) > 505:
        text = text[:500].rsplit(" ", 1)[0] + "…"
    return {"row": row, "col": col, "kind": kind, "text": text}


def by_id(rows, key):
    return {item[key]: item for item in rows}


def branch_ids(old):
    result = {}
    for cell in old["stickies"]:
        if cell["row"] == "ontology":
            result[cell["col"]] = cell["text"].split()[0]
    return result


def payment_label(conversion, service):
    code = conversion.get("PAYMENT_TYPE") or service.get("PAYMENT_TYPE", "")
    return PAYMENT.get(code, code)


def stage_title(state):
    return f"{state['id']} · {state['label']}"


def add_overlay(old, services, conversions, evidence, states):
    result = copy.deepcopy(old)
    result["meta"] = {
        "title": "MainExperts — CJM v4.0 · полный слой деталей",
        "subtitle": "22 ветви задач, 327 конечных задач и связанный коммерческий слой",
        "date": TODAY, "version": "4.0", "source": "CJM v3.0, глобальная онтология v2.0, агрегаты v4.0",
    }
    result["header"] = {
        **old["header"],
        "legend": LEGEND,
        "assumption": "Вход возможен на любой задаче. Оплата и интерфейсные решения являются гипотезами, даже если в поиске наблюдается коммерческое намерение.",
        "how_to_read": "Обзор состояний и сценарии переходов открываются отдельно. Здесь 22 колонки классов задач v3, каждая применима на нескольких стадиях.",
    }
    v4_rows = [{"id": ident, "label": label} for ident, label in ROW_DESCRIPTIONS.items()]
    for row in result["rows"]:
        if row["id"] == "payment":
            row["label"] = "Гипотезы оплаты v3"
        elif row["id"] == "external":
            row["label"] = "Внешние платежи v3"
    result["rows"] = [
        *(r for r in result["rows"] if r["id"] != "detail"), *v4_rows,
        *(r for r in result["rows"] if r["id"] == "detail"),
    ]
    for old_col, branch in branch_ids(old).items():
        service_options = [row for row in services if row["Q_ID"] == branch]
        states_here = ", ".join(s["id"] for s in states if branch in s["questions"])
        result["stickies"].append(as_note(f"{branch} встречается на маршруте: {states_here}.", old_col, "intent", "b"))
        for service in service_options:
            sid = service["SERVICE_ID"]
            free = conversions.get(f"C-{sid}-F", {})
            paid = conversions.get(f"C-{sid}-C") or conversions.get(f"C-{sid}-A") or {}
            base_evidence = evidence.get(sid, [])
            clue = summarize_clusters(base_evidence)[:136]
            extra = f" Кластеры из сводки: {clue}." if clue else ""
            result["stickies"].extend([
                as_note(f"{sid} · {short_evidence(base_evidence)}{extra}", old_col, "intent"),
                as_note(f"{sid} · {free.get('FREE_VALUE') or service['SELF_SERVICE']}", old_col, "free_v4", "g"),
                as_note(f"{sid} · {free.get('PAGE_URL_PATTERN') or 'страница задачи'} · {free.get('ELEMENT_ID', '')} · {free.get('CTA_PRIMARY') or 'связанная кнопка в каталоге CTA'}",
                        old_col, "interface_v4", "b"),
                as_note(f"{sid} · {service['DELEGATION_TRIGGER']}", old_col, "decision_v4", "ghost"),
                as_note(f"{sid} · {payment_label(paid, service)}. {service['FULFILMENT']}", old_col, "payment_v4", "ghost"),
            ])
    return result


def overview_yaml(states, transitions):
    lanes = [
        {"id": "person", "label": "Состояние пользователя", "style": 0},
        {"id": "checks", "label": "Результат и проверки", "style": 1},
    ]
    base = {
        "meta": {"title": "MainExperts — CJM v4.0 · обзор маршрута", "version": "4.0", "date": TODAY},
        "header": {
            "job": "Выбрать и реализовать доступный образовательный маршрут",
            "legend": LEGEND,
            "how_to_read": "У маршрута несколько точек входа. Пунктир показывает развилки и возвраты.",
        },
        "lanes": lanes, "stages": [], "flow": {"lane_height": 188, "nodes": [], "edges": []},
        "rows": [{"id": "linked", "label": "Связанные классы задач"}], "stickies": [],
    }
    pairs = [(0, 1, "Выбор"), (2, 3, "Осуществимость"), (4, 5, "Приём"), (6, len(states)-1, "Продолжение")]
    base["stages"].extend({"id": f"stage{a}", "from": a, "to": b, "label": name,
                           "color": ["#007c92", "#087d98", "#2256a8", "#2256a8"][i]}
                          for i, (a, b, name) in enumerate(pairs))
    for col, state in enumerate(states):
        ident = state["id"]
        base["flow"]["nodes"].extend([
            {"id": ident, "shape": "proc", "col": col, "lane": "person", "text": stage_title(state)},
            {"id": f"{ident}-out", "shape": "doc", "col": col, "lane": "checks", "text": state["result"]},
        ])
        base["flow"]["edges"].append({"from": ident, "to": f"{ident}-out", "ports": "bt", "arrow": False})
        base["stickies"].append(as_note(" · ".join(state["questions"]), col, "linked", "b"))
    base["flow"]["edges"].extend({"from": a["id"], "to": b["id"], "ports": "rl"} for a, b in zip(states, states[1:]))
    observed_edges = {(e["from"], e["to"]) for e in transitions}
    labels = [
        (2, 4, -54, "Условия выполнены"),
        (2, 1, -74, "Ограничение"),
        (5, 3, -80, "Условия оффера"),
        (5, 1, -104, "Отказ или истечение"),
        (8, 0, -129, "Новая цель"),
        (5, 7, -61, "Переезд не требуется"),
    ]
    for a, b, dy, label in labels:
        aa, bb = states[a]["id"], states[b]["id"]
        if (aa, bb) not in observed_edges:
            continue
        base["flow"]["edges"].append({
            "from": aa, "to": bb, "ports": "tt", "dash": True,
            "corridor": {"lane": "person", "dy": dy},
            "label": label, "label_at": "mid",
        })
    # Give corridor labels and returns room above the nodes without touching stage headers.
    base["flow"]["lane_height"] = 310
    return base


def slice_detail(full, stage):
    begin, end = stage["from"], stage["to"]
    chart = copy.deepcopy(full)
    chart["meta"]["title"] = f"MainExperts — CJM v4.0 · {DETAIL_SUBSETS[stage['id']]}"
    chart["header"] = {"how_to_read": "Классы задач показаны в раскладке v3. Точные исходы, услуги и детализация находятся в списке под картой."}
    stage_range = dict(stage)
    stage_range.update({"from": 0, "to": end - begin})
    chart["stages"] = [stage_range]
    chart["flow"]["nodes"] = [dict(n, col=n["col"] - begin) for n in chart["flow"]["nodes"] if begin <= n["col"] <= end]
    active_nodes = {n["id"] for n in chart["flow"]["nodes"]}
    chart["flow"]["edges"] = [e for e in chart["flow"]["edges"] if {e["from"], e["to"]} <= active_nodes]
    rows = {"ontology", "result", "free_v4", "interface_v4", "payment_v4"}
    chart["rows"] = [r for r in chart["rows"] if r["id"] in rows]
    chart["stickies"] = [dict(n, col=n["col"] - begin) for n in chart["stickies"]
                         if n["row"] in rows and begin <= n["col"] <= end]
    return chart


def raw_svg(svg, label):
    slug = "svg-" + hashlib.sha256(label.encode("utf-8")).hexdigest()[:10]
    fragment = svg[svg.index("<svg"):]
    return re.sub(r' id="([^"]+)"', lambda match: f' id="{slug}-{match[1]}"', fragment)


def chart_html(svg, label, overview=False):
    cls = "figure overview" if overview else "figure stage-map"
    return (f'<figure class="{cls}"><figcaption>{h(label)} '
            '<button class="scale" type="button" title="Увеличить карту">Масштаб</button></figcaption>'
            f'<div class="canvas">{raw_svg(svg, label)}</div></figure>')


def h(text):
    return html.escape(str(text if text is not None else ""), quote=True)


def row_html(values, heading=False):
    tag = "th" if heading else "td"
    return "<tr>" + "".join(f"<{tag}>{h(v)}</{tag}>" for v in values) + "</tr>"


def table_html(headers, rows):
    return f'<div class="table"><table><thead>{row_html(headers, True)}</thead><tbody>' + "".join(
        row_html(row) for row in rows
    ) + "</tbody></table></div>"


def kv_html(pairs):
    return "<dl>" + "".join(f"<dt>{h(key)}</dt><dd>{h(value)}</dd>" for key, value in pairs) + "</dl>"


def summarize_clusters(rows):
    counts = collections.Counter()
    for row in rows:
        counts.update(dict(row["CLUSTER_KEYS"]))
    return ", ".join(key for key, _ in counts.most_common(6))


def service_pairs(service, conversions, rows, states):
    sid = service["SERVICE_ID"]
    free = conversions.get(f"C-{sid}-F", {})
    paid = conversions.get(f"C-{sid}-C", {})
    alternative = conversions.get(f"C-{sid}-A", {})
    official = conversions.get(f"C-{sid}-O", {})
    basics = [
        ("Класс задачи · состояния", f"{service['Q_ID']} · " + ", ".join(s["id"] for s in states if service["Q_ID"] in s["questions"])),
        ("Продукт", service["PRODUCT_ID"] or "Отдельный продукт не сформирован"),
        ("Поисковые наблюдения", short_evidence(rows)),
        ("Выявленные кластеры", summarize_clusters(rows) or "См. матрицу «Страна × услуга»"),
        ("Самостоятельное решение", service["SELF_SERVICE"]),
        ("Бесплатный результат", free.get("FREE_VALUE") or service["SELF_SERVICE"]),
        ("Экран входа", free.get("PAGE_URL_PATTERN") or free.get("PAGE_TYPE") or "Связанная страница задачи"),
        ("CTA и элемент", f"{free.get('CONVERSION_ID', '')} · {free.get('ELEMENT_ID', '')} · {free.get('CTA_PRIMARY') or 'см. каталог'}"),
        ("Действие и следующий экран", f"{free.get('TARGET_ACTION', '')} · {free.get('CTA_TARGET', '')}"),
        ("Момент предложения услуги", service["DELEGATION_TRIGGER"]),
        ("Потенциальный результат услуги", service["PAID_VALUE"]),
        ("Сценарий оплаты", payment_label(paid or alternative, service)),
        ("Исполнение и выдача", (paid or alternative).get("FULFILMENT") or service["FULFILMENT"]),
        ("Бесплатная альтернатива", service["FREE_COMPETITOR"]),
        ("Риск", service["RISK"]),
    ]
    for key, conv in (("Платный вход", paid), ("Переход из бесплатного результата", alternative), ("Внешний маршрут", official)):
        if conv:
            basics.append((key, f"{conv.get('CTA_PRIMARY', '')} · {conv.get('CTA_TARGET', '')}"))
    return basics


def regional_pairs(region, conversions, loc, evidence):
    sid = region["service"]
    free = conversions.get(f"C-{sid}-F", {})
    direct = conversions.get(f"C-{sid}-C", {})
    def localized(conv):
        if not conv:
            return ""
        cid = conv.get("CONVERSION_ID", "")
        lang = region["locale"]
        change = loc.get((cid, lang)) or loc.get((cid, lang.split("-")[0])) or {}
        return change.get("CTA_PRIMARY") or conv.get("CTA_PRIMARY", "")
    matching = [x for x in evidence.get(sid, []) if x.get("SEARCH_MARKET") == region["id"]]
    count = sum(as_integer(a.get("UNIQUE_QUERIES")) for a in matching)
    evidence_text = (
        f'{formatted(count)} сопоставленных записей · D{max(levels(a.get("EVIDENCE_LEVEL")) for a in matching)} максимум'
        if count else "В доступной сводке по одноимённому рынку подтверждение отсутствует."
        if matching else "Нет сопоставленной сводки в выбранном поисковом рынке."
    )
    return [
        ("Точка входа", region["state"] + " · " + sid),
        ("Что уточнить", region["decision"]),
        ("Что пользователь получает бесплатно", region["free"]),
        ("Кнопка в проектной локали", localized(free) or "В официальном маршруте"),
        ("Когда показывать покупку", region["gate"]),
        ("Прямое действие, если доступно", localized(direct) or "Внешний маршрут или бесплатное завершение"),
        ("Наблюдения в одноимённом поисковом рынке", evidence_text),
        ("Кластеры в одноимённом поисковом рынке", summarize_clusters(matching) or "Сведений нет"),
    ]


def content_header():
    return (
        '<header class="page-header"><div class="brand">MainExperts</div><div class="header-date">26 ноября 2026</div>'
        '<h1>Карта образовательного пути</h1><p class="lead">CJM v4.0 · глобальный маршрут, точки оплаты и региональные сценарии</p></header>'
        '<nav aria-label="Разделы"><a href="#overview">Карта</a><a href="#transitions">Переходы</a>'
        '<a href="#services">Услуги</a><a href="#regions">14 систем</a><a href="#detailed">327 задач</a></nav>'
    )


def linked_stages(scenarios):
    state_rows = [(stage_title(state), ", ".join(state["questions"]), state["result"], state["choice"])
                  for state in scenarios["states"]]
    graph_rows = [(e["from"], e["to"], e["condition"]) for e in scenarios["transitions"]]
    return state_rows, graph_rows


def task_groups(old, registry):
    inherited = collections.defaultdict(list)
    branch_by_col = branch_ids(old)
    task_name = by_id(registry, "TASK_ID")
    observed = []
    restored_crossrefs = []
    for cell in old["stickies"]:
        if cell["row"] == "detail":
            ident, label = cell["text"].split(" · ", 1)
            old_name, old_result = label.split(" → ", 1)
            scope = branch_by_col[cell["col"]]
            reference = task_name[ident]
            assert reference["Q_ID"] == scope
            assert old_name == reference["TASK_NAME"]
            if old_result != reference["EXPECTED_RESULT"]:
                assert reference["EXPECTED_RESULT"].startswith(old_result)
                restored_crossrefs.append(ident)
            observed.append(ident)
            inherited[scope].append(reference)
    assert len(observed) == len(set(observed)) == 327
    assert set(observed) == set(task_name)
    assert set(restored_crossrefs) == {"Q12.07b", "Q22.05a"}
    return inherited, restored_crossrefs


def article_html(title, pairs, ident, addition=""):
    slug = f' id="{h(ident)}"' if ident else ""
    return f"<article{slug}><h3>{h(title)}</h3>{kv_html(pairs)}{addition}</article>"


def region_sources_html(region):
    source = f'<p><a href="{h(region["official"])}">{h(region["provider"])}</a>'
    if region.get("benchmark"):
        source += f' · <a href="{h(region["benchmark"])}">{h(region["benchmark_name"])}</a>'
    return source + f' · <a href="#{h(region["service"])}">Карточка услуги</a></p>'


def detail_tasks_html(old, task_registry, stage_maps):
    result = ['<section id="detailed"><h2>Конечные задачи и результаты</h2>'
              '<p>Пять детальных карт в раскладке предыдущей CJM. 327 задач сохранены и сверены с глобальной онтологией по коду и названию. У Q12.07b и Q22.05a восстановлены усечённые ссылки на связанные задачи. Ветви Q встречаются в нескольких состояниях маршрута.</p>']
    for stage in old["stages"]:
        name = DETAIL_SUBSETS[stage["id"]]
        result.append(f'<h3 id="detail-{stage["id"]}">{h(name)}</h3>')
        result.append(chart_html(stage_maps[stage["id"]], f"{name} · детальная карта"))
        for col, qid in branch_ids(old).items():
            if not stage["from"] <= col <= stage["to"]:
                continue
            group = task_registry[qid]
            title = qid + " · " + group[0]["Q_NAME"]
            result.append(f'<details class="details" id="{qid}"><summary>{h(title)} · {len(group)}</summary>')
            result.append(table_html(("Код", "Задача", "Проверяемый результат"), [
                (task["TASK_ID"], task["TASK_NAME"], task["EXPECTED_RESULT"]) for task in group
            ]))
            result.append("</details>")
    return "".join(result) + "</section>"


def make_html(config, out, old, scenarios, services, conversions, loc, evidence, task_registry, svg, stages):
    state_rows, graph_rows = linked_stages(scenarios)
    region_pair_rows = [(region, regional_pairs(region, conversions, loc, evidence)) for region in scenarios["regions"]]
    sections = [
        content_header(),
        '<section id="overview"><h2>Обзор маршрута</h2>'
        '<p class="notice">Вход и бесплатное завершение возможны на любой задаче. Этапы J описывают состояния маршрута. Классы задач Q и платные гипотезы P привязаны к ним отдельными связями.</p>',
        chart_html(svg, "Глобальная CJM · основные развилки и возвраты", overview=True),
        "</section>",
        '<section id="transitions"><h2>Переходы и решения</h2>',
        table_html(("Состояние", "Классы задач", "Проверяемый результат", "Развилка"), state_rows),
        '<h3>Условия переходов</h3>',
        table_html(("Из", "В", "Условие"), graph_rows),
        '<p>Вход из поиска может сразу открыть требования известного набора или статус уже поданной заявки. Проверки бюджета, признания, допуска и мобильности идут параллельно, когда применимы. План действий хранит неизвестное как отдельный статус.</p>'
        '<p>Порядок покупки. До оплаты показать состав результата, цена, срок, исполнитель, условия возврата и бесплатный путь. После оплаты показать подтверждение заказа, статус исполнения и результат. При необходимости предусмотрены исправление и возврат. События оплаты и выдачи учитываются отдельно.</p>'
        '<p>Платежи организации и госоргану проходят в их официальном канале. Покупка партнёрской услуги направляет к партнёру с раскрытием связи. MainExperts принимает собственный платёж только за подтверждённый состав результата. Для несовершеннолетних учитываются роли и полномочия, для чувствительных документов собирается необходимый минимум.</p>'
        '</section><section id="services"><h2>Карты услуг и оплаты</h2>'
        '<p>Сохранены 22 исходные точки оплаты. P23–P26 добавлены как отдельные продуктовые гипотезы. В каждой карточке показан самостоятельный маршрут и принимаемый результат возможной покупки. Полная выборка формулировок, рынков, кластеров и источников находится в аналитической базе и матрице «Страна × услуга».</p>'
        '<p class="notice">D0–D4 относятся к качеству поискового или внешнего подтверждения. Для D5 нужны покупки MainExperts, для D6 нужны подтверждённые прибыльность и масштабируемость. Бесплатный сценарий может завершить путь целиком.</p><div class="jump">',
        "".join(f'<a href="#{h(s["SERVICE_ID"])}">{h(s["SERVICE_ID"])}</a>' for s in services),
        "</div>",
    ]
    for service in services:
        sid = service["SERVICE_ID"]
        title = sid + " · " + service["SERVICE_NAME"]
        matched = evidence.get(sid, [])
        regional_table = ""
        if matched:
            regional_table = (
                f'<details class="details print-hide"><summary>Поисковые рынки и кластеры · {len(matched)}</summary>'
                '<p>ZZ-RU обозначает папку исследования России с неустановленным рынком поиска. D0 означает отсутствие подтверждения в использованной сводке.</p>'
                + table_html(COUNTRY_SUMMARY_COLUMNS, country_summary_rows(matched)) + "</details>"
            )
        sections.append(article_html(title, service_pairs(service, conversions, matched, scenarios["states"]), sid, regional_table))
    sections.extend([
        '</section><section id="regions"><h2>Сценарии 14 образовательных систем</h2>'
        '<p>Каждая карточка демонстрирует одну локальную развилку. Официальная ссылка подтверждает процедуру для применимого случая. Язык кнопки выбран для проектного интерфейса. Страна обучения, страна поиска и гражданство заполняются отдельно. Поисковая строка в карточке относится к одноимённому рынку, когда доступна сводка.</p>'
        '<div class="grid case-grid">',
        "".join(article_html(
            f"{region['title']} · {region['pathway']}", pairs, f"market-{region['id']}",
            region_sources_html(region),
        ) for region, pairs in region_pair_rows),
        "</div></section>",
        detail_tasks_html(old, task_registry, stages),
        f'<footer><p>Преемственность · CJM v3.0, глобальная онтология v2.0 и связанная аналитическая база v4.0. '
        f'Векторные карты построены <a href="{h(GENERATOR_URL)}">оригинальным генератором MainExperts</a>.</p></footer>',
    ])
    template = (config / "cjm-template.html").read_text(encoding="utf-8")
    out.write_text(template.replace("<!-- PUBLICATION -->", "\n".join(sections)), encoding="utf-8")


def md_table(headers, rows):
    def esc(value):
        return str(value or "").replace("\n", " ").replace("|", r"\|")
    def line(values):
        return "| " + " | ".join(esc(v) for v in values) + " |\n"
    return line(headers) + line(["---"] * len(headers)) + "".join(line(r) for r in rows)


def make_md(path, old, scenarios, services, conversions, loc, evidence, task_registry):
    st_rows, graph_rows = linked_stages(scenarios)
    parts = [
        "# MainExperts · CJM v4.0\n\n26 ноября 2026. Карта реализации образовательного пути, поисковой релевантности и проверяемых гипотез оплаты.\n",
        "## Карта и форматы\n\n"
        "Откройте обзор [SVG](mainexperts-cjm-v4.svg) или полный [HTML](mainexperts-cjm-v4.html). "
        "Прямая сборка обзорного SVG доступна из [overview.yaml](details/overview.yaml). "
        "Накопительные данные всех ветвей в [journey-v4.yaml](journey-v4.yaml), "
        "состояния, связи и сценарии в [journey-v4-links.yaml](journey-v4-links.yaml).\n",
        "## Состояния и развилки\n\n"
        "J — состояние образовательного маршрута. Q — класс задач. P — услуга-кандидат. "
        "Связи J и Q допускают несколько состояний для одного класса. "
        "Вход, параллельные проверки и бесплатный выход возможны в любой точке. "
        "Неопределённая применимость требует источника или уточнения, решение выносит уполномоченная сторона. "
        "Оффер, принятие и зачисление подтверждаются по отдельности. "
        "Учащийся, абитуриент, плательщик и представитель могут быть разными людьми.\n\n",
        md_table(("Состояние", "Классы задач", "Результат", "Развилка"), st_rows),
        "\n### Переходы\n\n",
        md_table(("Из", "В", "Условие"), graph_rows),
        "\n## Клетки оплаты и выдача\n\n"
        "Типовой вход начинается с поисковой формулировки. Далее — страница задачи → бесплатное действие и самостоятельный результат → "
        "потребность в проверке или делегировании → карточка фиксированного результата → оплата → исполнение → приёмка. "
        "Для прямого коммерческого входа сформированное предложение может быть доступно сразу. "
        "Оплата MainExperts, счёт партнёра и сбор организации или государственного органа — разные события. "
        "До покупки показывать цену, результат, срок, критерии приёмки, исполнителя и бесплатный путь. "
        "Регистрацию и чувствительные документы запрашивать по необходимости. "
        "Связь с услугой обозначает гипотезу монетизации. D5 и D6 требуют собственных транзакционных и финансовых данных. "
        "Оригинальные запросы и их сводки см. в аналитической базе и матрице «Страна × услуга».\n",
    ]
    for service in services:
        sid = service["SERVICE_ID"]
        parts.append(f"\n### {sid} · {service['SERVICE_NAME']}\n\n")
        parts.append(md_table(("Поле", "Значение"), service_pairs(service, conversions, evidence.get(sid, []), scenarios["states"])))
    parts.append("\n## Локальные сценарии\n\nПроцедуры привязаны к стране обучения. Поисковые наблюдения в таблице относятся к одноимённому рынку, если есть агрегаты. Язык CTA выбирается для проектной локали.\n")
    for region in scenarios["regions"]:
        parts.append(f"\n### {region['title']} · {region['pathway']}\n\n")
        parts.append(md_table(("Поле", "Значение"), regional_pairs(region, conversions, loc, evidence)))
        links = f"[{region['provider']}]({region['official']})"
        if region.get("benchmark"):
            links += f" · [{region['benchmark_name']}]({region['benchmark']})"
        parts.append(f"\n{links}\n")
    parts.append("\n## Исходная декомпозиция задач\n\nВсе 327 задач CJM v3 совпали с глобальной онтологией по коду и названию. В результатах Q12.07b и Q22.05a восстановлены две ссылки, обрезанные в исходной визуализации.\n")
    for stage in old["stages"]:
        stage_id = stage["id"]
        parts.append(f"\n### {DETAIL_SUBSETS[stage_id]}\n\n[Детальная векторная карта](details/{stage_id}.svg) · [входные данные генератора](details/{stage_id}.yaml)\n")
        for col, qid in branch_ids(old).items():
            if stage["from"] <= col <= stage["to"]:
                group = task_registry[qid]
                parts.append(f"\n#### {qid} · {group[0]['Q_NAME']}\n\n")
                parts.append(md_table(("Код", "Задача", "Проверяемый результат"), [
                    (task["TASK_ID"], task["TASK_NAME"], task["EXPECTED_RESULT"]) for task in group
                ]))
    parts.append(f"\n## Воспроизведение\n\nСхемы отрисованы оригинальным генератором MainExperts на ревизии `{GENERATOR_COMMIT}`. "
                 "SVG содержит контуры шрифта. HTML выводит текстовую версию оригинальных векторных карт и связанные таблицы. "
                 "PDF печатает обзор и детальные таблицы с разбиением на страницы. Точный порядок запуска указан в README конвейера.\n\n"
                 f"[Исходный генератор]({GENERATOR_URL})\n")
    path.write_text("".join(parts), encoding="utf-8")


def loader(skill):
    sys.path.insert(0, str(skill / "scripts"))
    from cjm_map import fonts, model, render
    return fonts, model, render


def render_original(path, out, fonts, model, render):
    data = model.load(str(path))
    if data["_warnings"]:
        raise ValueError(f"{path}: {data['_warnings']}")
    fonts.missing.clear()
    outline = render.build_svg(data, "outline")
    if fonts.missing:
        raise ValueError(f"Glyphs missing in {path}: {fonts.missing}")
    out.write_text(outline, encoding="utf-8")
    return render.build_svg(data, "text")


def pdf_print(html_path, output):
    from weasyprint import HTML
    printable = html_path.read_text(encoding="utf-8").replace("<details class=", "<details open class=")
    start = printable.index("<svg")
    finish = printable.index("</svg>") + len("</svg>")
    overview = printable[start:finish]
    # WeasyPrint can paint the original white halo over thin route labels.
    overview = overview.replace(' stroke="#fafafa" stroke-width="4" stroke-linejoin="round" paint-order="stroke"', "")
    # Fit the original stage blocks and geometry on A4 by setting the print viewport below its repeated legend.
    title = re.search(r'<text[^>]* y="([0-9.]+)"[^>]*>Блок-схема: единый поток слева направо</text>', overview)
    box = re.search(r'height="(\d+)" viewBox="0 0 (\d+) (\d+)"', overview)
    if title and box:
        crop = int(float(title[1])) + 52
        size = int(box[3]) - crop
        resized = overview[:box.start()] + f'height="{size}" viewBox="0 {crop} {box[2]} {size}"' + overview[box.end():]
        printable = printable[:start] + resized + printable[finish:]
    HTML(string=printable, base_url=str(html_path.parent)).write_pdf(str(output), pdf_tags=True)


def git_rev(skill):
    probe = subprocess.run(["git", "-C", str(skill), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return probe.stdout.strip() if probe.returncode == 0 else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    current = Path(__file__).resolve().parent
    ap.add_argument("--skill", type=Path, required=True, help="Original .claude/skills/cjm-map directory")
    ap.add_argument("--config", type=Path, default=current / "config")
    ap.add_argument("--prior", type=Path, default=current / "config/cjm-v3-baseline.yaml")
    ap.add_argument("--data", type=Path, default=current.parent / "data")
    ap.add_argument("--out", type=Path, default=current.parent / "cjm")
    ap.add_argument("--skip-pdf", action="store_true")
    args = ap.parse_args()
    skill = args.skill.resolve()
    if (skill / "README.md").is_file() is False:
        raise FileNotFoundError(f"Original generator with README missing: {skill}")
    if (revision := git_rev(skill)) and revision != GENERATOR_COMMIT:
        raise ValueError(f"Original generator revision {revision} != {GENERATOR_COMMIT}")
    out = args.out.resolve()
    details = out / "details"
    details.mkdir(parents=True, exist_ok=True)
    old = read_yaml(args.prior)
    scenarios = read_yaml(args.config / "cjm-scenarios.yaml")
    services = read_csv(args.config / "services.tsv")
    conversions = by_id(read_csv(args.config / "conversions.tsv"), "CONVERSION_ID")
    loc = {(row["CONVERSION_ID"], row["LANGUAGE"]): row
           for row in read_csv(args.config / "cta_localizations.tsv")}
    evidence_rows = read_csv(args.data / "country_service.csv")
    evidence = collect_evidence(evidence_rows, read_csv(args.data / "country_cluster.csv"))
    task_registry, restored = task_groups(old, read_csv(args.config / "tasks.tsv"))
    assert len(services) == 26 and len(scenarios["regions"]) == 14 and len(scenarios["states"]) == 9
    assert all(f'C-{row["SERVICE_ID"]}-F' in conversions for row in services)
    assert {r["Q_ID"] for r in services} == set(branch_ids(old).values())
    assert {p["CJM_ID"] for p in services} <= {s["id"] for s in scenarios["states"]}
    assert all(r["Q_ID"] in next(s["questions"] for s in scenarios["states"] if s["id"] == r["CJM_ID"])
               for r in services)
    assert all(t["from"] in {s["id"] for s in scenarios["states"]} and
               t["to"] in {s["id"] for s in scenarios["states"]} for t in scenarios["transitions"])
    assert all(r["service"] in {p["SERVICE_ID"] for p in services} and
               r["state"] in {s["id"] for s in scenarios["states"]} for r in scenarios["regions"])
    full = add_overlay(old, services, conversions, evidence, scenarios["states"])
    preserved = [item for item in full["stickies"] if item["row"] not in ROW_DESCRIPTIONS]
    assert preserved == old["stickies"]
    assert full["flow"] == old["flow"]
    write_yaml(out / "journey-v4.yaml", full)
    anchors = {
        "meta": {"publication": "MainExperts — CJM v4.0", "date": TODAY,
                 "original_cjm": hashlib.sha256(args.prior.read_bytes()).hexdigest(),
                 "original_renderer": GENERATOR_COMMIT,
                 "source_cjm": "journey-v3.yaml", "published_file": "mainexperts-cjm-v4.html"},
        "states": scenarios["states"], "transitions": scenarios["transitions"],
        "regions": scenarios["regions"],
        "stage_detail_maps": [{"id": s["id"], "filename": f"details/{s['id']}.svg", "input": f"details/{s['id']}.yaml"}
                              for s in old["stages"]],
        "payment_links": [
            {
                "service_id": row["SERVICE_ID"], "product_id": row["PRODUCT_ID"], "main_state_id": row["CJM_ID"],
                "q_id": row["Q_ID"], "payment_type": row["PAYMENT_TYPE"],
                "conversion_ids": [key for key, c in conversions.items() if c["SERVICE_ID"] == row["SERVICE_ID"]],
                "markets_with_search_observations": len({
                    obs["SEARCH_MARKET"] for obs in evidence.get(row["SERVICE_ID"], [])
                    if obs["SEARCH_MARKET"] != "ZZ-RU" and as_integer(obs.get("UNIQUE_QUERIES"))
                }),
                "highest_search_evidence": max((obs.get("EVIDENCE_LEVEL") for obs in evidence.get(row["SERVICE_ID"], [])),
                                               key=levels, default=None),
            } for row in services
        ],
    }
    assert len({c["service_id"] for c in anchors["payment_links"]}) == len(services)
    write_yaml(out / "journey-v4-links.yaml", anchors)
    fonts, model, render = loader(skill)
    model.load(str(out / "journey-v4.yaml"))
    overview = details / "overview.yaml"
    write_yaml(overview, overview_yaml(scenarios["states"], scenarios["transitions"]))
    svg = render_original(overview, out / "mainexperts-cjm-v4.svg", fonts, model, render)
    stages = {}
    for stage in old["stages"]:
        ident = stage["id"]
        model_path = details / f"{ident}.yaml"
        write_yaml(model_path, slice_detail(full, stage))
        stages[ident] = render_original(model_path, details / f"{ident}.svg", fonts, model, render)
    html_path = out / "mainexperts-cjm-v4.html"
    make_html(args.config, html_path, old, scenarios, services, conversions, loc, evidence, task_registry, svg, stages)
    make_md(out / "mainexperts-cjm-v4.md", old, scenarios, services, conversions, loc, evidence, task_registry)
    if not args.skip_pdf:
        pdf_print(html_path, out / "mainexperts-cjm-v4.pdf")
    log = {
        "original_generator_revision": GENERATOR_COMMIT,
        "old_stickies_preserved": len(preserved),
        "original_pay_cells": sum(row["row"] == "payment" for row in preserved),
        "new_service_hypotheses": len(services) - 22,
        "states": len(scenarios["states"]),
        "transitions": len(scenarios["transitions"]),
        "regional_scenarios": len(scenarios["regions"]),
        "original_tasks_verified": sum(map(len, task_registry.values())),
        "task_cross_references_restored_in_tables": restored,
        "services_checked": len(services),
        "main_cjm_validated": True,
        "svg_files": len(stages) + 1,
        "country_service_aggregate_rows_with_queries": sum(
            bool(as_integer(row.get("UNIQUE_QUERIES"))) for items in evidence.values() for row in items
        ),
    }
    (out / "cjm-validation.json").write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
