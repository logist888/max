"""Produce country/service evidence, traceable examples and coverage exports."""
import argparse
import csv
import json
from pathlib import Path

import duckdb

from warehouse import TARGET_MARKETS, quote_path

CSV_OPTS = "(format csv, header true, force_quote *)"
PAIRS = """
create or replace temp view in_scope as
select *, coalesce(search_market,case when source_region='RU' then 'ZZ-RU' end) display_market
from query_journey where search_market in ('RU','GB','US','CA','CH','FR','IT','ES','AE','SG','HK','CN','DE','AU')
                         or (search_market is null and source_region='RU');
create or replace temp table country_service_core as
with counts as (
  select display_market,service_id,
         count(*) unique_queries, count(*) filter(where evidence_level='D3') d3_queries,
         count(*) filter(where evidence_level='D2') d2_queries,
         count(*) filter(where evidence_level='D1') d1_queries,
         max(evidence_level) evidence_level, count(distinct source_id) representative_sources,
         string_agg(distinct language,'; ' order by language) languages,
         string_agg(distinct search_engine,'; ' order by search_engine) engines,
         count(distinct cluster_id) clusters, count(distinct subcluster_id) subclusters,
         count(*) filter(where volume is not null) with_volume,
         count(*) filter(where conversion_id is not null) with_conversion
  from in_scope where service_id is not null and evidence_level in ('D1','D2','D3') group by all
)
select m.display_market as search_market, s.service_id,s.service_name,s.cjm_id,s.assessment,s.product_id,
       case when m.display_market='ZZ-RU' then 'География поиска не определена. Папка RU'
            when m.display_market='RU' then 'Рынок RU только при явном коде в выгрузке'
            else 'Явный код рынка' end market_scope,
       coalesce(c.evidence_level,'D0') evidence_level,
       coalesce(c.unique_queries,0) unique_queries, coalesce(c.d3_queries,0) d3_queries,
       coalesce(c.d2_queries,0) d2_queries, coalesce(c.d1_queries,0) d1_queries,
       coalesce(c.representative_sources,0) representative_sources, c.languages,c.engines,
       coalesce(c.clusters,0) clusters,coalesce(c.subclusters,0) subclusters,
       coalesce(c.with_volume,0) with_volume,coalesce(c.with_conversion,0) with_conversion,
       s.self_service,s.delegation_trigger,s.paid_value,s.payment_type,s.fulfilment,s.free_competitor,s.risk
from (select unnest(['RU','GB','US','CA','CH','FR','IT','ES','AE','SG','HK','CN','DE','AU','ZZ-RU']) display_market) m
cross join services s left join counts c using(display_market,service_id);
"""

EXAMPLES = """
with sample_pool as (
 select display_market as search_market,service_id,query_id,query_raw,query_translation,language,destination,search_engine,
        volume,volume_metric,cpc,kd,cluster_base_id,cluster_id,subcluster_id,intent_id,task_id,source_id,source_url,source_region,
        source_date,observed_date,evidence_level, confidence, page_url_pattern, element_id, cta_primary, event, payment_type,
        row_number() over(partition by display_market,service_id,evidence_level
                          order by try_cast(confidence as double) desc nulls last, language is null,
                            query_raw not like '% %', volume desc nulls last, query_id) rk
 from in_scope where service_id is not null and evidence_level in ('D1','D2','D3')
) select * exclude (rk) from sample_pool where rk<=3 order by search_market,service_id,evidence_level desc,rk
"""

MARKETS = """
select coalesce(search_market,'∅') as search_market, search_engine, volume_metric,
       count(*) distinct_market_engine_pairs,count(distinct query_normalized) distinct_texts,
       count(*) filter (where volume is not null) with_volume,
       count(*) filter (where cpc is not null) with_cpc,count(*) filter (where kd is not null) with_kd,
       count(*) filter (where relevance='excluded_explicit') excluded,
       count(*) filter (where cluster_id is null) without_cluster,
       count(*) filter (where evidence_level='D1') d1, count(*) filter (where evidence_level='D2') d2,
       count(*) filter (where evidence_level='D3') d3
from query_journey group by all order by 1,2,3
"""

def get_stats(c):
    expressions = {
        "sources":"select count(*) from sources where status in ('processed','partial_schema')",
        "sources_with_ref":"select count(*) from sources",
        "source_regions":"select count(distinct region) from sources where status in ('processed','partial_schema')",
        "raw_rows":"select count(*) from observations",
        "raw_query_rows":"select count(*) from query_observation_keys",
        "empty_query_rows":"select count(*) from observations where query_normalized is null",
        "unique_market_engine_queries":"select count(*) from queries",
        "unique_query_texts":"select count(distinct query_normalized) from queries",
        "raw_query_spelling_count":"select count(distinct query_raw) from observations where query_normalized is not null",
        "verified_market_count":"select count(distinct search_market) from queries",
        "unknown_market":"select count(*) from queries where search_market is null",
        "unknown_search_engine":"select count(*) from queries where search_engine is null",
        "unknown_language":"select count(*) from query_journey where language is null or language in ('und','unknown','')",
        "null_destination":"select count(*) from query_journey where destination is null",
        "duplicate_file_count":"select count(*)-count(distinct sha256) from sources where sha256 is not null",
        "flagged_partial_exports":"select count(*) from sources where incomplete_filename",
        "branches_observed":"select count(distinct q_id) from query_journey where cluster_id is not null",
        "canonical_tasks_registered":"select count(*) from tasks",
        "canonical_tasks_observed":"select count(distinct v.task_id) from query_journey v join tasks t using(task_id) where v.cluster_id is not null",
        "base_clusters_catalog":"select count(*) from cluster_catalog",
        "base_clusters_observed":"select count(distinct cluster_base_id) from query_journey where cluster_id is not null",
        "clusters_observed":"select count(*) from cluster_instances",
        "subclusters_observed":"select count(*) from regional_subclusters",
        "mapped_queries":"select count(*) from query_journey where cluster_id is not null",
        "rejected_or_unmapped":"select count(*) from query_journey where cluster_id is null",
        "services_catalog":"select count(*) from services",
        "services_with_evidence":"select count(distinct service_id) from query_journey where evidence_level in ('D1','D2','D3')",
        "services_with_D3":"select count(distinct service_id) from query_journey where evidence_level='D3'",
        "products_catalog":"select count(*) from products",
        "elements_catalog":"select count(*) from elements",
        "elements_observed":"select count(distinct element_id) from query_journey",
        "conversions_catalog":"select (select count(*) from conversions)+(select count(*) from neutral_conversions)",
        "conversions_observed":"select count(distinct conversion_id) from query_journey",
        "localizations_catalog":"select (select count(*) from cta_localizations)+(select count(*) from neutral_cta_localizations)",
        "with_translation":"select count(*) from query_journey where query_translation is not null",
        "with_conversion":"select count(*) from query_journey where conversion_id is not null",
        "D1":"select count(*) from query_journey where evidence_level='D1'",
        "D2":"select count(*) from query_journey where evidence_level='D2'",
        "D3":"select count(*) from query_journey where evidence_level='D3'",
        "machine_D3":"select count(*) from commercial_review",
        "reviewed_D3_demotions":"select count(*) from commercial_review where retained_evidence_level in ('D0','D1','D2')",
        "above_D3":"select count(*) from query_journey where evidence_level in ('D4','D5','D6')",
    }
    return {k:c.execute(sql).fetchone()[0] for k,sql in expressions.items()}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    c=duckdb.connect(str(a.db),read_only=True)
    c.execute("set threads=7; set memory_limit='3GB';")
    c.execute(PAIRS)
    shipments = {
        "source_inventory":"select * from sources order by region, title",
        "source_sheets":"select * from source_sheets order by source_id,sheet",
        "source_folders":"select region as source_folder, count(*) files, sum(query_rows) query_rows, sum(bytes_local) AS bytes_total, count(distinct nominal_domain) nominal_domains, sum(case when incomplete_filename then 1 else 0 end) flagged_partial from sources where status in ('processed','partial_schema') group by region order by region",
        "file_duplicates":"select sha256, count(*) copies, string_agg(title,' | ' order by title) filenames, string_agg(source_id,' | ' order by title) source_ids from sources where sha256 is not null group by sha256 having count(*)>1",
        "search_markets": MARKETS,
        "country_service": "select * from country_service_core order by search_market,service_id",
        "country_service_examples":EXAMPLES,
        "country_cluster":"""select display_market search_market,service_id,language,search_engine,cluster_id,subcluster_id,intent_id,
                          count(*) unique_queries,max(evidence_level) evidence_level,
                          sum(1) filter(where volume is not null) with_volume
                          from in_scope where cluster_id is not null and evidence_level in ('D1','D2','D3')
                          group by all order by display_market,service_id,language,search_engine,cluster_id""",
        "commercial_review_counts":"select reason,machine_service_id,count(*) pairs from commercial_review group by all order by 1,2",
        "cluster_instances":"select * from cluster_instances order by cluster_id",
        "regional_subclusters":"select * from regional_subclusters order by subcluster_id",
        "task_coverage":"""with seen as (select task_id, count(*) pairs, count(*) filter (where evidence_level='D3') d3 from query_journey where cluster_id is not null group by task_id)
                          select t.*,coalesce(pairs,0) observed_pairs,coalesce(d3,0) d3_pairs from tasks t left join seen using(task_id) order by task_id""",
        "service_summary":"""with v as (select service_id,count(*) unique_queries,max(evidence_level) evidence_level,
                            count(*) filter(where evidence_level='D3') d3,count(*) filter(where evidence_level='D2') d2,
                            count(*) filter(where evidence_level='D1') d1,
                            count(distinct search_market) filter(where evidence_level in ('D1','D2','D3')) markets,
                            count(distinct search_market) filter(where evidence_level='D3') d3_markets,
                            count(distinct cluster_id) clusters from query_journey
                            where evidence_level in ('D1','D2','D3') group by service_id)
                            select s.*,coalesce(v.evidence_level,'D0') evidence_level,coalesce(v.unique_queries,0) unique_queries,
                            coalesce(v.d3,0) d3,coalesce(v.d2,0) d2,coalesce(v.d1,0) d1,coalesce(v.markets,0) markets,
                            coalesce(v.d3_markets,0) d3_markets,coalesce(v.clusters,0) clusters
                            from services s left join v using(service_id) order by s.service_id""",
        "scope_status":"""select coalesce(relevance,'∅') relevance,evidence_level,count(*) pairs,
                          count(*) filter(where cluster_id is not null) clustered from query_journey group by all order by 3 desc""",
        "missing_conversion":"""select distinct cluster_id,service_id,intent_id,q_id from query_journey
             where evidence_level in ('D2','D3') and conversion_id is null order by service_id,intent_id,cluster_id""",
    }
    for name,sql in shipments.items():
        file=a.output/(name+".csv")
        # The exchange schema uses the same uppercase names as the user's requested matrix.
        projection=c.execute(f"select * from ({sql}) t limit 0").description
        cols=", ".join('"' + d[0] + '" as "' + d[0].upper() + '"' for d in projection)
        c.execute(f"copy (select {cols} from ({sql}) ship) to {quote_path(file)} {CSV_OPTS}")
    stats=get_stats(c)
    (a.output/"coverage.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2))
    print(stats,flush=True)

if __name__=="__main__":
    main()
