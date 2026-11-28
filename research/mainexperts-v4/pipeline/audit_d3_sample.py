#!/usr/bin/env python3
"""Extract deterministic, coverage-oriented D3 candidates for human review."""

import argparse
import csv
import json
from pathlib import Path

import duckdb


def collect(conn, labels, cap):
    conn.execute("""
        create temp table eligible as
        select q.query_id,q.query_raw,q.query_normalized,q.target_url,q.source_id,q.source_url,
               q.volume,q.volume_metric,q.search_market,q.search_engine,
               l.language,l.intent_id,l.cluster_id,l.cluster_base_id,l.q_id,l.service_id,
               l.confidence,l.limitations,
               coalesce(l.service_id,'∅') as service_scope,
               coalesce(l.language,'∅') as language_scope,
               coalesce(q.search_market,'∅') as market_scope
        from read_parquet(?) l
        join queries q using(query_id)
        where l.evidence_level='D3'
    """, [[str(p.resolve()) for p in labels]])
    conn.execute("""
        create temp table strata as
        select service_scope,language_scope,market_scope,count(*) as candidate_count
        from eligible group by all
    """)
    return conn.execute("""
        with largest_strata as (
            select * from strata order by candidate_count desc, service_scope,language_scope,market_scope
            limit ?
        ), ranked as (
            select e.*,st.candidate_count,
                row_number() over (partition by e.service_scope order by e.query_id) service_rn,
                row_number() over (partition by e.language_scope order by e.query_id) language_rn,
                row_number() over (partition by e.market_scope order by e.query_id) market_rn,
                row_number() over (
                    partition by e.service_scope,e.market_scope,e.language_scope order by e.query_id
                ) stratum_rn,
                row_number() over (
                    partition by e.service_scope
                    order by e.volume desc nulls last, e.query_id
                ) service_volume_rn,
                t.candidate_count is not null as biggest
            from eligible e join strata st using(service_scope,language_scope,market_scope)
            left join largest_strata t using(service_scope,language_scope,market_scope)
        )
        select *,
            service_rn=1 as covers_service,
            language_rn=1 as covers_language,
            market_rn=1 as covers_market,
            biggest and stratum_rn<=2 as covers_prevalent_stratum,
            service_volume_rn=1 as covers_high_volume_service
        from ranked
        where covers_service or covers_language or covers_market or
              covers_prevalent_stratum or covers_high_volume_service
        order by covers_prevalent_stratum desc,candidate_count desc,
                 covers_high_volume_service desc,service_scope,market_scope,language_scope,query_id
    """, [cap])


def write_result(conn, path):
    headers = [d[0].upper() for d in conn.description]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(conn.fetchall())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--database", required=True, type=Path)
    p.add_argument("--classified", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--prevalent-strata", default=32, type=int)
    p.add_argument("--export-candidates", action="store_true", help="Also write every candidate to the private audit directory")
    a = p.parse_args()
    if a.prevalent_strata < 1:
        p.error("--prevalent-strata must be positive")
    labels = sorted(a.classified.glob("*.parquet"))
    if not labels:
        p.error("No completed classification parquet files")
    a.output.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(a.database), read_only=True)
    conn.execute("set threads=4; set memory_limit='1.2GB';")
    result = collect(conn, labels, a.prevalent_strata)
    write_result(result, a.output / "d3_audit_sample.csv")
    write_result(conn.execute("select * from strata order by candidate_count desc,service_scope,language_scope,market_scope"),
                 a.output / "d3_audit_strata.csv")
    if a.export_candidates:
        write_result(conn.execute("select * from eligible order by service_scope,market_scope,language_scope,query_id"),
                     a.output / "d3_audit_candidates.csv")
    totals = conn.execute("""
        select count(*),count(distinct service_scope),count(distinct language_scope),count(distinct market_scope)
        from eligible
    """).fetchone()
    with (a.output / "d3_audit_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(dict(files=len(labels), d3_pairs=totals[0], services=totals[1],
                       languages=totals[2], markets=totals[3], top_strata=a.prevalent_strata), handle, indent=2)
    print(f"{len(labels)} completed partitions, {totals[0]} D3 rows")


if __name__ == "__main__":
    main()
