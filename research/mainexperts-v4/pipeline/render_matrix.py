"""Render the evidence matrix as Markdown and provide workbook-ready data."""
import argparse
import csv
import json
from pathlib import Path

MARKETS = {"RU":"Россия", "GB":"Великобритания", "US":"США", "CA":"Канада",
           "CH":"Швейцария", "FR":"Франция", "IT":"Италия", "ES":"Испания",
           "AE":"ОАЭ", "SG":"Сингапур", "HK":"Гонконг", "CN":"Китай",
           "DE":"Германия", "AU":"Австралия", "ZZ-RU":"Папка RU · география неизвестна"}
NUMERIC = {
    "VOLUME","CPC","KD","D3_QUERIES","D2_QUERIES","D1_QUERIES","WITH_VOLUME","WITH_CONVERSION",
    "CLUSTERS","SUBCLUSTERS","UNIQUE_QUERIES","RAW_ROWS","QUERY_ROWS","ROWS","FILES","BYTES_TOTAL",
    "NOMINAL_DOMAINS","REPRESENTATIVE_SOURCES","BYTES_LOCAL","BYTES_CATALOG","OBSERVED_PAIRS","D3_PAIRS",
    "D1","D2","D3","MARKETS","D3_MARKETS","DISTINCT_MARKET_ENGINE_PAIRS","DISTINCT_TEXTS","WITH_CPC","WITH_KD",
    "EXCLUDED","WITHOUT_CLUSTER","PAIRS","CLUSTERED","FLAGGED_PARTIAL",
}

def read(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t" if path.suffix==".tsv" else ","))

def cell(value):
    return str(value or "—").replace("|","\\|").replace("\n"," ").replace("\r"," ")

def service_doc(data, output):
    cs, examples = read(data/"country_service.csv"), read(data/"country_service_examples.csv")
    summaries = read(data/"service_summary.csv")
    stats = json.loads((data/"coverage.json").read_text())
    by_pair={}
    for e in examples:
        by_pair.setdefault((e["SEARCH_MARKET"],e["SERVICE_ID"]),[]).append(e)
    via_pairs={}
    for e in cs:
        via_pairs.setdefault(e["SERVICE_ID"],{})[e["SEARCH_MARKET"]]=e
    lines=[
        "# MainExperts. Матрица «рынок поиска × услуга»",
        "",
        "Версия 4.0 · 26 ноября 2026 года",
        "",
        f"В базе {stats['sources']:,} выгрузок, {stats['raw_query_rows']:,} строк с исходными фразами и "
        f"{stats['unique_market_engine_queries']:,} уникальных пар запроса и поискового контекста. "
        "Ниже 14 целевых рынков плюс отдельная группа русскоязычных источников без подтверждённой географии.",
        "",
        "Рынок берётся из поля поставщика, включая отдельно помеченный верхний поисковый рынок агрегированных выгрузок. "
        "Страна обучения может отличаться от страны поиска. D0 показывает отсутствие подтверждения в обработанном срезе. "
        "D1 показывает информационную потребность, D2 — инструмент или персональный результат, D3 — поисковое намерение купить "
        "самостоятельную услугу. Число фраз показывает покрытие данного корпуса. Частотность приводится только для исходного примера, "
        "с указанием поисковика и типа метрики. Значения разных поисковиков не суммируются.",
        "",
        "### Сводка по услугам",
        "",
        "| Услуга | Уровень | Контексты D1–D3 | Из них D3 | Рынки с D3 |",
        "|---|---|---:|---:|---:|",
    ]
    lines.extend(f"| {r['SERVICE_ID']} · {cell(r['SERVICE_NAME'])} | {r['EVIDENCE_LEVEL']} | {r['UNIQUE_QUERIES']} | {r['D3']} | {r['D3_MARKETS']} |" for r in summaries)
    for s in summaries:
        id=s["SERVICE_ID"]
        lines += ["",f"## {id}. {s['SERVICE_NAME']}","",
                  f"**Самостоятельно.** {s['SELF_SERVICE']}  ",
                  f"**Когда делегировать.** {s['DELEGATION_TRIGGER']}  ",
                  f"**Платный результат.** {s['PAID_VALUE']}  ",
                  f"**Оплата и получение.** {s['PAYMENT_TYPE']}. {s['FULFILMENT']}",
                  "",
                  "| Рынок поиска | Уровень · фразы · D3 | Языки | Исходный пример · частотность · намерение | Элемент и действие |",
                  "|---|---:|---|---|---|"]
        for market,label in MARKETS.items():
            r=via_pairs[id][market]
            cand=by_pair.get((market,id),[])
            if cand:
                e=cand[0]
                detail=(f"{cell(e['QUERY_RAW'])} · {cell(e['VOLUME'])} ({cell(e['SEARCH_ENGINE'])}; "
                        f"{cell(e['VOLUME_METRIC'])}) · {cell(e['INTENT_ID'])}, {cell(e['CLUSTER_ID'])} "
                        f"[источник]({e['SOURCE_URL']})")
                action=f"{cell(e['ELEMENT_ID'])} · {cell(e['CTA_PRIMARY'])}"
            else:
                detail="Пробел доказательности для этой пары"
                action="—"
            lines.append(f"| {label} | {r['EVIDENCE_LEVEL']} · {r['UNIQUE_QUERIES']} · {r['D3_QUERIES']} | {cell(r['LANGUAGES'])} | {detail} | {action} |")
    lines += ["","В книге Excel на вкладке «Исходные фразы» доступно до трёх примеров каждого достигнутого уровня по каждой паре. "
              "В CSV и базе сохранены трассировка до файла и исходной строки, все наблюдения, CPC и KD при наличии. "
              "Коммерческие выводы относятся к представленным доменам и формулировкам, а локальная применимость услуги проверяется "
              "по стране обучения, языку и правилам исполнения."]
    output.write_text("\n".join(lines)+"\n",encoding="utf-8")

def make_workbooks(data, config, output):
    def get(filename):
        path=(config if filename.endswith(".tsv") else data)/filename
        rows=read(path)
        if rows:
            keys=list(rows[0])
        else:
            with path.open(encoding="utf-8-sig",newline="") as f:
                keys=next(csv.reader(f,delimiter="\t" if path.suffix==".tsv" else ","))
        def scalar(k,v):
            if v=="" or v is None:
                return None
            if k in NUMERIC:
                try:
                    return int(v) if v.isdecimal() else float(v)
                except ValueError:
                    pass
            return v
        return [keys]+[[scalar(k,r.get(k)) for k in keys] for r in rows]
    wbooks={
        "03-analytical-overview.xlsx":("Управленческая сводка",[
          ("Услуги","service_summary.csv"),("Исходные папки","source_folders.csv"),
          ("Рынки поиска","search_markets.csv"),("Отсев и классы","scope_status.csv"),
          ("Файлы и источники","source_inventory.csv"),("Кластеры","cluster_instances.csv"),
          ("Задачи v2","task_coverage.csv"),("Продукты","products.tsv")]),
        "04-country-service.xlsx":("Рынки поиска и услуги",[
          ("Матрица рынок услуга","country_service.csv"),("Исходные фразы","country_service_examples.csv"),
          ("Услуги","service_summary.csv"),("Локальные правила","regions_ontology.tsv")]),
        "05-interface-conversion.xlsx":("Интерфейсы, действия и события",[
          ("Переходы и действия","conversions.tsv"),("Элементы","elements.tsv"),
          ("Привязки намерений","conversion_intents.tsv"),("Локализации CTA","cta_localizations.tsv"),
          ("Рынки и языки","markets_language.tsv"),("Внешние и нейтральные","neutral_conversions.tsv"),("Пробелы интерфейса","missing_conversion.csv")]),
    }
    content={}
    for name,(title,sheets) in wbooks.items():
        content[name]={"title":title,"sheets":[{"name":sn,"rows":get(file)} for sn,file in sheets]}
    output.write_text(json.dumps(content,ensure_ascii=False),encoding="utf-8")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--docs",type=Path,required=True)
    p.add_argument("--config",type=Path,required=True)
    p.add_argument("--json",type=Path,required=True)
    a=p.parse_args()
    service_doc(a.data,a.docs/"04-country-service.md")
    make_workbooks(a.data,a.config,a.json)

if __name__=="__main__":
    main()
