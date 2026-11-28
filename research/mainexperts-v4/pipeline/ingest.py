"""Stream Drive exports into typed Parquet, retaining every original record."""
import argparse
import csv
import hashlib
import io
import json
import re
import unicodedata
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

import openpyxl
import pyarrow as pa
import pyarrow.parquet as pq

ALIASES = {
    "query_raw": ("keyword", "keywords", "query", "ключевое слово", "ключевые слова", "запрос", "фраза", "search term", "keyword phrase"),
    "search_market_raw": ("country", "search country", "market", "database", "страна", "гео"),
    "location_raw": ("location", "search location", "region", "регион"),
    "language_raw": ("language", "язык"),
    "volume_raw": ("volume", "search volume", "search volume (monthly)", "avg monthly searches", "avg. monthly searches", "frequency", "частотность", "объем", "объём (volume)", "частота", "показы"),
    "exact_frequency_raw": ("[!frequency]", "!frequency", "[!частотность]", "exact frequency"),
    "cpc_raw": ("cpc", "cpc (usd)", "cpc usd", "ср. цена за клик"),
    "kd_raw": ("kd", "keyword difficulty", "difficulty"),
    "target_raw": ("current url", "relevant url", "релевантный url", "url", "ranking url", "landing page", "целевая страница"),
    "observed_raw": ("updated", "date", "last update", "last seen", "дата", "обновлено"),
    "engine_raw": ("search engine", "engine", "поисковая система"),
    "position_raw": ("current position", "position", "average position", "позиция"),
    "branded": ("branded",), "navigational": ("navigational",),
    "informational": ("informational",), "commercial": ("commercial",),
    "transactional": ("transactional",),
}
STRING_FIELDS = ["query_raw", "query_normalized", "search_market", "search_market_raw", "location_raw",
                 "language_raw", "search_engine", "engine_raw", "volume_raw", "top_volume_raw", "exact_frequency_raw",
                 "cpc_raw", "kd_raw", "volume_metric", "target_raw", "target_url", "observed_raw",
                 "raw_cells"]
SCHEMA = pa.schema(
    [("source_id", pa.string()), ("sheet", pa.string()), ("row_no", pa.int64())]
    + [(n, pa.string()) for n in STRING_FIELDS]
    + [(n, pa.float64()) for n in ("volume", "broad_frequency", "cpc", "kd", "position")]
    + [("observed_date", pa.string())]
    + [(n, pa.bool_()) for n in ("branded", "navigational", "informational", "commercial", "transactional")]
)
CODE = re.compile(r"^[A-Z]{2}$")
DOMAIN = re.compile(r"(?:https?://)?((?:[a-z0-9][a-z0-9-]*\.)+[a-z]{2,})(?=[^a-z0-9.]|$)", re.I)
EXPORT_DATE = re.compile(r"(20\d\d-\d\d-\d\d)[_ T]")
SPACE = re.compile(r"\s+")
GOOGLE = re.compile(r"\bgoogle\b", re.I)
YANDEX = re.compile(r"yandex|яндекс", re.I)
COUNTRY_CODE = {"UK": "GB", "EL": "GR", "XK": "XK"}

def scalar(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value) if value is not None else None

def clean(value):
    return value.strip() or None if value else None

def textnorm(value):
    return SPACE.sub(" ", unicodedata.normalize("NFKC", value).casefold()).strip()

def number(value):
    if not value:
        return None
    try:
        result = float(value.strip().replace("\u00a0", "").replace(" ", "").replace(",", "."))
    except ValueError:
        return None
    return result if 0 <= result < float("inf") else None

def boolean(value):
    return {"true": True, "false": False, "yes": True, "no": False, "1": True, "0": False}.get((value or "").lower())

def find_date(value):
    try:
        return date.fromisoformat((value or "")[:10]).isoformat()
    except ValueError:
        match = re.match(r"(\d\d)[./](\d\d)[./](20\d\d)", value or "")
        if match:
            try:
                return date(int(match[3]), int(match[2]), int(match[1])).isoformat()
            except ValueError:
                pass
    return None

def market(value):
    s = (value or "").strip().upper()
    return COUNTRY_CODE.get(s, s) if CODE.fullmatch(s) else None

def engine(value):
    if YANDEX.search(value or ""):
        return "Yandex"
    if GOOGLE.search(value or ""):
        return "Google"
    for v in ("Baidu", "Bing", "Naver", "Yahoo", "DuckDuckGo"):
        if v.lower() in (value or "").lower():
            return v
    return None

def input_tables(path):
    if path.suffix == ".xlsx":
        book = openpyxl.load_workbook(path, read_only=True, data_only=True)
        try:
            for sheet in book:
                yield sheet.title, iter(sheet.values), "xlsx"
        finally:
            book.close()
        return
    with path.open("rb") as stream:
        head = stream.read(16384)
        if head[:2] in (b"\xff\xfe", b"\xfe\xff"):
            encoding = "utf-16"
        elif head.startswith(b'"\x00') or head.startswith(b'K\x00'):
            encoding = "utf-16-le"
        else:
            encoding = "utf-8-sig"
            try:
                head.decode(encoding)
            except UnicodeDecodeError as exc:
                if exc.end < len(head) - 3:
                    encoding = "cp1251"
        sample = head.decode(encoding, errors="replace").splitlines()[0]
        delimiter = max(("\t", ";", ","), key=sample.count)
        stream.seek(0)
        with io.TextIOWrapper(stream, encoding=encoding, errors="strict", newline="") as text:
            yield "", csv.reader(text, delimiter=delimiter), encoding

def header_map(header):
    normalized = {textnorm(s): i for i,s in enumerate(header) if s}
    return {k: next((normalized[a] for a in names if a in normalized), None) for k,names in ALIASES.items()}

def records(table, hdr, source, sheet, start):
    positions = header_map(hdr)
    domain = source["nominal_domain"]
    header_keys = {textnorm(s or ""): i for i,s in enumerate(hdr)}
    ahrefs_local = {"serp features", "current url", "kd"}.issubset(header_keys)
    ahrefs_top = {"top location code", "top location's volume", "organic traffic"}.issubset(header_keys)
    ahrefs = ahrefs_local or ahrefs_top
    keys_pattern = positions["exact_frequency_raw"] is not None and positions["target_raw"] is not None
    style = ("Ahrefs (top location)" if ahrefs_top else "Ahrefs") if ahrefs else ("Keys-style" if keys_pattern else "unidentified")
    default_engine = engine(source["title"]) or ("Google" if ahrefs else None)
    query_column = positions["query_raw"]
    counters = {"rows": 0, "query_rows": 0, "missing_query": 0, "unmapped_rows": 0, "ragged_rows": 0}
    for row_no, values in enumerate(table, start=start):
        cells = [scalar(v) for v in values]
        if not any(v not in (None, "") for v in cells):
            continue
        counters["rows"] += 1
        counters["ragged_rows"] += len(cells) != len(hdr)
        raw = {k: cells[p] if p is not None and p < len(cells) else None for k,p in positions.items()}
        if ahrefs_top:
            for key, col in (("search_market_raw","top location code"), ("location_raw","top location"), ("top_volume_raw","top location's volume")):
                pos = header_keys[col]
                raw[key] = cells[pos] if pos < len(cells) else None
        query = raw["query_raw"]
        key = textnorm(query) if query else None
        if key:
            counters["query_rows"] += 1
        elif query_column is not None:
            counters["missing_query"] += 1
        else:
            counters["unmapped_rows"] += 1
        target = clean(raw["target_raw"])
        if target and target.startswith("/") and domain:
            target = "https://" + domain + target
        if target and not target.startswith(("http://", "https://", "/")) and DOMAIN.match(target):
            target = "https://" + target
        if not source["nominal_domain"] and target:
            source["nominal_domain"] = urlparse(target).hostname
        exact = number(raw["exact_frequency_raw"])
        broad = number(raw["volume_raw"])
        volume = exact if keys_pattern else (number(raw.get("top_volume_raw")) if ahrefs_top else broad)
        normalized = raw | {
            "source_id": source["id"], "sheet": sheet, "row_no": row_no,
            "query_normalized": key, "search_market": market(raw["search_market_raw"]),
            "search_engine": engine(raw["engine_raw"]) or default_engine,
            "target_url": target, "volume": volume, "broad_frequency": broad if keys_pattern else None,
            "volume_metric": "keys_exact" if keys_pattern else ("ahrefs_volume" if ahrefs else ("vendor_unspecified" if volume is not None else None)),
            "observed_date": find_date(raw["observed_raw"]), "cpc": number(raw["cpc_raw"]),
            "kd": number(raw["kd_raw"]), "position": number(raw["position_raw"]),
            "raw_cells": json.dumps(cells, ensure_ascii=False, separators=(",", ":")),
        }
        normalized.update({k: boolean(raw[k]) for k in ("branded", "navigational", "informational", "commercial", "transactional")})
        yield normalized
    source["sheets"].append({"sheet": sheet, "header": hdr, "header_row": start - 1,
                             "schema": style, "engine_default": default_engine, **counters})

def ingest_one(job):
    source, input_root, stage_root = job
    match = DOMAIN.search(source["title"])
    date_match = EXPORT_DATE.search(source["title"])
    source.update(nominal_domain=match[1].lower() if match else None, sheets=[],
                  export_date=date_match[1] if date_match else None)
    if source["region"] == "ONTO":
        source["status"] = "reference_inventory"
        return source
    source["incomplete_filename"] = bool(re.search(r"лимит|[0-9]+к\s+из", source["title"], re.I))
    inmeta = input_root / "manifests" / (source["id"] + ".json")
    sources = list((input_root / "raw").glob(source["id"] + ".*"))
    path = next((p for p in sources if p.suffix in {".csv", ".xlsx"}), None)
    if path is None:
        source["status"] = "unavailable"
        source["issue"] = json.loads(inmeta.read_text()).get("error") if inmeta.exists() else "local source not present"
        return source
    source["bytes_local"] = path.stat().st_size
    source["sha256"] = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
    if source["mime_type"] != "application/vnd.google-apps.spreadsheet" and source["size"] and source["bytes_local"] != int(source["size"]):
        source.update(status="size_mismatch", issue="binary transport differs from Drive metadata")
        return source
    partial = stage_root / (source["id"] + ".partial")
    finished = stage_root / (source["id"] + ".parquet")
    try:
        with pq.ParquetWriter(partial, SCHEMA, compression="zstd") as writer:
            for sheet, table, enc in input_tables(path):
                first = []
                for _, row in zip(range(12), table):
                    first.append(row)
                    if header_map([scalar(v) for v in row])["query_raw"] is not None:
                        break
                if not first:
                    continue
                header = [scalar(v) for v in first[-1]]
                if header_map(header)["query_raw"] is None:
                    from itertools import chain
                    header = [scalar(v) for v in first[0]]
                    table = chain(first[1:], table)
                    start = 2
                else:
                    start = len(first) + 1
                    if len(first) > 1:
                        source.setdefault("preamble", {})[sheet] = [[scalar(v) for v in row] for row in first[:-1]]
                source.setdefault("encodings", {})[sheet] = enc
                batch = []
                for record in records(table, header, source, sheet, start):
                    batch.append(record)
                    if len(batch) >= 20000:
                        writer.write_table(pa.Table.from_pylist(batch, SCHEMA))
                        batch.clear()
                if batch:
                    writer.write_table(pa.Table.from_pylist(batch, SCHEMA))
        partial.replace(finished)
        queries = sum(x["query_rows"] for x in source["sheets"])
        unparsed = sum(x["unmapped_rows"] for x in source["sheets"])
        source["status"] = "partial_schema" if queries and unparsed else ("processed" if queries else "no_query_header")
        if unparsed:
            source["issue"] = "unmapped worksheet columns, original rows retained"
    except Exception as exc:
        partial.unlink(missing_ok=True)
        source.update(status="parse_error", issue=f"{type(exc).__name__}: {exc}")
    return source

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--reuse", action="store_true")
    args = parser.parse_args()
    args.stage.mkdir(parents=True, exist_ok=True)
    sources = json.loads((args.input / "inventory.json").read_text())
    for row in sources:
        row.setdefault("size", None)
    existing = args.stage / "sources.json"
    previous = {x["id"]: x for x in json.loads(existing.read_text())} if args.reuse and existing.exists() else {}
    previous = {k:v for k,v in previous.items() if v["status"] in {"processed", "partial_schema", "reference_inventory"}
                and (v["status"] == "reference_inventory" or (args.stage / (k+".parquet")).exists())}
    jobs = [(s,args.input,args.stage) for s in sources if s["id"] not in previous]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        done = list(previous.values())
        for i, result in enumerate(pool.map(ingest_one, jobs), 1):
            done.append(result)
            if i % 20 == 0:
                print(f"Staged {i}/{len(jobs)}", flush=True)
    existing.write_text(json.dumps(done, ensure_ascii=False, indent=2))
    from collections import Counter
    print(Counter(x["status"] for x in done))
    print("Raw nonempty rows:", sum(y["rows"] for x in done for y in x["sheets"]))

if __name__ == "__main__":
    main()
