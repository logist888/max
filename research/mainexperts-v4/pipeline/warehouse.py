"""Build the reproducible DuckDB warehouse and run batch classification."""
import argparse
import csv
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

BASE = Path(__file__).resolve().parent
TARGET_MARKETS = ("RU", "GB", "US", "CA", "CH", "FR", "IT", "ES", "AE", "SG", "HK", "CN", "DE", "AU")
AUDIT_FIELDS = ["LANGUAGE", "INTENT_ID", "CLUSTER_BASE_ID", "CLUSTER_ID", "SUBCLUSTER_ID", "Q_ID", "TASK_ID", "TASK_HINT",
                "SERVICE_ID", "RELEVANCE", "CONFIDENCE", "SECONDARY_CLUSTERS", "EVIDENCE_LEVEL", "LEARNING_LEVEL",
                "PROGRAM_TYPE", "ROLE", "DESTINATION_HINT", "QUERY_TRANSLATION", "LIMITATIONS", "ACTION_PAYEE", "LANGUAGE_SOURCE"]
CLASS_SCHEMA = pa.schema([("query_id", pa.string())] + [(x.lower(), pa.string()) for x in AUDIT_FIELDS])

OBSERVATION_VIEWS = """
create or replace view query_observation_keys as
select o.* exclude(volume_metric),
       case when sh.schema = 'Ahrefs (top location)' then 'ahrefs_top_location_volume' else o.volume_metric end as volume_metric,
       src.* exclude(source_id), sh.schema as source_schema,
       case when search_market is null then 'unknown-' || source_region || '-' || coalesce(volume_metric,'unidentified') end as unknown_scope,
       md5(concat_ws(chr(31), query_normalized, coalesce(search_market,'~'),
         coalesce(search_engine,'~'),
         case when search_market is null then source_region || '-' || coalesce(volume_metric,'unidentified') else '~' end)) as query_id
from observations o join (select source_id, region as source_region, export_date, source_url, sha256 from sources) src using(source_id)
left join (select source_id, sheet, schema from source_sheets) sh using(source_id,sheet)
where query_normalized is not null;

create or replace table queries as
select query_id, query_raw, query_normalized, search_market, unknown_scope, search_engine, source_id, sheet, row_no,
       source_url, source_region, export_date, observed_date, volume, cpc, kd, volume_metric, target_url,
       language_raw, branded, navigational, informational, commercial, transactional,
       observation_count, source_count
from (
  select *,
    row_number() over w as row_rank,
    count(*) over (partition by query_id) as observation_count,
    count(distinct coalesce(sha256,source_id)) over (partition by query_id) as source_count
  from query_observation_keys
  window w as (partition by query_id order by
      (volume is not null) desc,
      case source_schema when 'Ahrefs' then 2 when 'Ahrefs (top location)' then 1 else 2 end desc,
      coalesce(observed_date,export_date) desc nulls last,
      (target_url is not null) desc,(language_raw is not null) desc, source_id,sheet,row_no)
)
where row_rank=1;
"""

def quote_path(path):
    return "'" + str(path.resolve()).replace("'", "''") + "'"

def repair_duplicate_provenance(connection):
    connection.execute("""
      create or replace table duplicate_content as
      select sha256, count(*) copies, count(distinct nominal_domain) domains,
             string_agg(source_id, ', ' order by source_id) source_ids
      from sources where sha256 is not null group by sha256 having count(*)>1;
      update observations set target_url = null where starts_with(target_raw,'/')
      and source_id in (select source_id from sources join duplicate_content using(sha256) where domains>1);
    """)

def load_stage(connection, stage, work, threads):
    records = json.loads((stage / "sources.json").read_text())
    source_rows, sheet_rows = [], []
    for row in records:
        source_rows.append({
            "source_id": row["id"], "region": row["region"], "title": row["title"],
            "source_url": row["url"], "mime_type": row["mime_type"], "bytes_catalog": int(row["size"] or 0),
            "bytes_local": row.get("bytes_local"), "sha256": row.get("sha256"),
            "export_date": row.get("export_date"), "drive_modified": row["modified_time"],
            "nominal_domain": row.get("nominal_domain"), "status": row["status"],
            "incomplete_filename": bool(row.get("incomplete_filename")),
            "issue": row.get("issue"), "sheets": len(row["sheets"]),
            "rows": sum(t["rows"] for t in row["sheets"]),
            "query_rows": sum(t["query_rows"] for t in row["sheets"]),
            "unmapped_rows": sum(t["unmapped_rows"] for t in row["sheets"]),
        })
        for s in row["sheets"]:
            sheet_rows.append({
                "source_id": row["id"], "sheet": s["sheet"], "schema": s["schema"], "engine_default": s["engine_default"],
                "encoding": row.get("encodings",{}).get(s["sheet"]), "header_row": s["header_row"],
                "header_json": json.dumps(s["header"],ensure_ascii=False),
                "preamble_json": json.dumps(row.get("preamble",{}).get(s["sheet"]),ensure_ascii=False),
                **{k:s[k] for k in ("rows","query_rows","missing_query","unmapped_rows","ragged_rows")},
            })
    connection.register("source_arrow", pa.Table.from_pylist(source_rows))
    connection.register("sheet_arrow", pa.Table.from_pylist(sheet_rows))
    connection.execute("create or replace table sources as select * from source_arrow")
    connection.execute("create or replace table source_sheets as select * from sheet_arrow")
    connection.execute(f"create or replace table observations as select * from read_parquet({quote_path(stage/'*.parquet')}, union_by_name=true)")
    repair_duplicate_provenance(connection)
    connection.execute(OBSERVATION_VIEWS)
    write_partitions(connection, work)

def write_partitions(connection, work):
    partitions = work / "query_partitions"
    partitions.mkdir(parents=True, exist_ok=True)
    connection.execute(f"""copy (
      select query_id, query_raw, query_normalized, search_market, target_url,
             language_raw, branded, navigational, commercial, transactional,
             cast(hash(query_id)%36 as int) batch
      from queries) to {quote_path(partitions)} (format parquet, partition_by(batch), overwrite_or_ignore)""")
    print(connection.execute("select count(*), count(distinct query_normalized), count(*) filter (where search_market is not null) from queries").fetchone(), flush=True)

def parse_classification(job):
    part, output = job
    from classify import classify
    import inspect
    sig = inspect.signature(classify).parameters
    available_optional = {"language_raw","lang_hint","language_hint","provider_language","branded","navigational","commercial","transactional"}
    accepts = set(sig) & available_optional
    processed = 0
    tmp = output.with_suffix(".partial")
    with pq.ParquetWriter(tmp, CLASS_SCHEMA, compression="zstd") as writer:
        for batch in pq.ParquetFile(part).iter_batches(batch_size=8000):
            cards = []
            cols = batch.to_pydict()
            for i, kid in enumerate(cols["query_id"]):
                opt = {}
                for arg in accepts:
                    src = "language_raw" if arg in {"language_raw","lang_hint","language_hint","provider_language"} else arg
                    opt[arg] = cols[src][i]
                out = classify(cols["query_normalized"][i], cols["target_url"][i] or "", cols["search_market"][i], **opt)
                row = {"query_id":kid}
                for name in AUDIT_FIELDS:
                    v = out.get(name)
                    if isinstance(v, (tuple,list,dict,set)):
                        v = json.dumps(sorted(v) if isinstance(v,set) else v, ensure_ascii=False, separators=(",",":"))
                    row[name.lower()] = str(v) if v not in (None,"") else None
                cards.append(row)
            writer.write_table(pa.Table.from_pylist(cards, CLASS_SCHEMA))
            processed += len(cards)
    tmp.replace(output)
    return processed

def classify_partitions(work, workers, resume):
    files = sorted((work / "query_partitions").glob("batch=*/*.parquet"))
    out = work / "classified"; out.mkdir(exist_ok=True)
    jobs = [(p, out / (p.parent.name + "_" + p.name)) for p in files]
    if resume:
        jobs = [j for j in jobs if not j[1].exists()]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i, n in enumerate(pool.map(parse_classification, jobs),1):
            print(f"Classified partition {i}/{len(jobs)}: {n}", flush=True)

def load_classification(connection, work):
    connection.execute(f"create or replace table query_labels as select * from read_parquet({quote_path(work/'classified'/'*.parquet')})")
    n, lab, unique = connection.execute("select (select count(*) from queries),count(*),count(distinct query_id) from query_labels").fetchone()
    if n != lab or n != unique:
        raise ValueError(f"Classification coverage mismatch {n=}, {lab=}, {unique=}")
    for table in ("tasks","elements","services","products","conversions","cluster_catalog","gap_register","gap_sources",
                  "regions_ontology","regional_documents","objectives_ontology","commercial_benchmarks","cta_localizations","conversion_intents","markets_language","neutral_conversions","neutral_cta_localizations","query_translations"):
        f = BASE / "config" / (table + ".tsv")
        if f.exists():
            connection.execute(f"create or replace table {table} as select * from read_csv({quote_path(f)},delim='\t',header=true,all_varchar=true)")
    connection.execute("create table if not exists query_translations(query_normalized varchar,query_translation varchar)")
    connection.execute((BASE / "evidence_calibration.sql").read_text())
    connection.execute((BASE / "matrix.sql").read_text())
    connection.execute("checkpoint")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase",choices=("stage","classify","integrate"))
    p.add_argument("--stage",type=Path,required=True)
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--db",type=Path,required=True)
    p.add_argument("--workers",type=int,default=7)
    p.add_argument("--resume",action="store_true")
    a = p.parse_args()
    a.work.mkdir(parents=True,exist_ok=True)
    if a.phase == "classify":
        classify_partitions(a.work,a.workers,a.resume)
        return
    c = duckdb.connect(str(a.db))
    c.execute(f"set threads={a.workers}; set memory_limit='3GB'; set preserve_insertion_order=false;")
    if a.phase == "stage":
        load_stage(c,a.stage,a.work,a.workers)
    else:
        load_classification(c,a.work)

if __name__ == "__main__":
    main()
