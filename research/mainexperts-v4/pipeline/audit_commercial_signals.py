#!/usr/bin/env python3
"""Independent strict lexical cross-check, excluded from the main classification."""

import argparse
import csv
import json
from pathlib import Path

import duckdb

CONFIG = Path(__file__).resolve().parent / "config"


def write_provenance(connection, stage, partitions, output):
    registry = json.loads((stage / "sources.json").read_text(encoding="utf-8"))
    source_by_id = {row["id"]: row for row in registry}
    candidates = output / "commercial_control_examples.csv"
    matches = connection.execute("""
        with source_rows as (
            select o.*, s.region as source_region, cast(s.export_date as varchar) as export_date
            from read_parquet(?) o join read_json_auto(?) s on s.id=o.source_id
        ), observations as (
            select *, md5(concat_ws(chr(31), query_normalized, coalesce(search_market,'~'),
                            coalesce(search_engine,'~'),
                            case when search_market is null then source_region || '-' ||
                                coalesce(volume_metric,'unidentified') else '~' end)) as query_id
            from source_rows s where query_normalized is not null
        ), hits as (
            select e.service_id, e.search_market, e.query_id, q.query_normalized, q.target_url,
                   s.source_id, s.volume, s.volume_metric, s.search_engine, s.observed_date,
                   row_number() over(partition by e.service_id, e.query_id order by
                      (s.volume is not null) desc, coalesce(s.observed_date,s.export_date) desc nulls last,
                      (s.target_url is not null) desc, (s.language_raw is not null) desc,
                      s.source_id, s.sheet, s.row_no) as i
            from read_csv_auto(?) e join read_parquet(?) q on e.query_id=q.query_id
               join observations s on e.query_id=s.query_id
        )
        select * exclude(i) from hits where i=1 order by 1,2,4
    """, [str(stage / "*.parquet"), str(stage / "sources.json"), str(candidates), partitions])
    headers = [col[0].upper() for col in matches.description] + ["SOURCE_URL", "SOURCE_NAME"]
    with (output / "commercial_control_provenance.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in matches.fetchall():
            source = source_by_id[row[5]]
            writer.writerow(row + (source["url"], source["title"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partitions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage", type=Path, help="Staged inputs and sources.json, for provenance export")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with (CONFIG / "commercial_control_patterns.tsv").open(encoding="utf-8") as f:
        patterns = list(csv.DictReader(f, delimiter="\t"))

    glob = str(args.partitions.resolve() / "batch=*" / "*.parquet")
    connection = duckdb.connect()
    connection.execute("set threads=4")
    connection.execute("set memory_limit='1.5GB'")
    query_columns = ["SERVICE_ID", "SEARCH_MARKET", "QUERY_ID", "QUERY_RAW"]
    with (args.output / "commercial_control_examples.csv").open("w", encoding="utf-8", newline="") as ef, (
        args.output / "commercial_control_counts.csv"
    ).open("w", encoding="utf-8", newline="") as af:
        examples = csv.writer(ef)
        aggregates = csv.writer(af)
        examples.writerow(query_columns)
        aggregates.writerow(("SERVICE_ID", "SEARCH_MARKET", "CANDIDATE_PAIRS"))
        for rule in patterns:
            sid = rule["SERVICE_ID"]
            connection.execute("""
                create or replace temp table candidates as
                select query_id, query_raw, search_market
                from read_parquet(?)
                where regexp_matches(query_normalized, ?)
            """, [glob, rule["REGEX"]])
            results = connection.execute("""
                select coalesce(search_market, 'und'), count(*) from candidates group by all order by 1
            """).fetchall()
            for market, candidate_count in results:
                aggregates.writerow((sid, market, candidate_count))
            for market, kid, raw in connection.execute("""
                select coalesce(search_market, 'und'), query_id, query_raw from candidates
                qualify row_number() over (
                    partition by search_market order by length(query_raw), query_id
                ) <= 7 order by search_market nulls last, length(query_raw), query_id
            """).fetchall():
                examples.writerow((sid, market, kid, raw))
            print(sid, sum(n for _, n in results), flush=True)
    if args.stage:
        write_provenance(connection, args.stage, glob, args.output)


if __name__ == "__main__":
    main()
