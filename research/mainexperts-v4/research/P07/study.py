"""P07 audit against every normalized query and each associated raw observation."""
import argparse
import csv
import json
from pathlib import Path

import duckdb

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('database', type=Path)
parser.add_argument('out', type=Path)
parser.add_argument('--rules', type=Path, default=Path(__file__).with_name('rules.tsv'))
args = parser.parse_args()
args.out.mkdir(exist_ok=True, parents=True)
c = duckdb.connect()
c.execute("set threads=8; set memory_limit='3GB'; set preserve_insertion_order=false")
c.execute(f"attach '{str(args.database.resolve()).replace(chr(39), chr(39) * 2)}' as corpus (read_only)")
with args.rules.open() as file:
    rules = list(csv.DictReader(file, delimiter='\t'))
families = ('K022','K026','K027','K028','K123')
family_sql = '(' + ','.join(map(repr,families)) + ')'
def literal(value):
    return "'" + value.replace("'", "''") + "'"

case = ' '.join(f"when regexp_matches(search_text,{literal(row['pattern'])}) then {literal(row['cluster'])}" for row in rules)
secondary = r'(^|[^0-9])(K022|K026|K027|K028|K123)([^0-9]|$)'
matcher = r'^https?://(?:www\.)?([^/:?#]+)'
exclude = r'(?i)(?:\bcrossword\b|\bword search\b|\bminecraft\b|\btcgs?\b|школьный баскетбол рейтинг|топ школ магии|рейтинг гимназий в игре|\bcollege football (?:power )?rank|\brankings? college football|football rankings?|basketball rankings?|ncaa rankings?|volleyball rankings?|football polls?|\bhigh school dxd\b|школ[а-я]* магии)'
c.execute(f"""
create temp table lexical as
select query_id, lexical_cluster from (
  select query_id, case {case} end lexical_cluster
  from (select query_id, lower(regexp_replace(query_normalized,'[‘’`''´]', ' ', 'g')) search_text from corpus.queries)
) matched where lexical_cluster is not null
""")
c.execute(f"""
create temp table selected_ids as
select query_id from lexical union
select query_id from corpus.query_labels where service_id='P07' or cluster_base_id in {family_sql} or regexp_matches(coalesce(secondary_clusters,''), '{secondary}')
""")
c.execute(f"""
create temp table candidates as
with flags as (
select q.query_id, q.query_normalized, l.language, l.q_id prior_q, l.task_id prior_task,
l.cluster_base_id prior_cluster, l.service_id prior_service,l.intent_id prior_intent,l.evidence_level prior_d,l.secondary_clusters,
l.service_id='P07' is_direct, l.cluster_base_id in {family_sql} is_family,
regexp_extract(coalesce(l.secondary_clusters,''), '{secondary}',2) secondary,
lx.lexical_cluster,
regexp_matches(q.query_normalized, ?) excluded_pattern
from selected_ids i join corpus.queries q using(query_id)
left join corpus.query_labels l using(query_id) left join lexical lx using(query_id)
)
select *,case
 when excluded_pattern then 'excluded'
 when lexical_cluster is not null then 'rule_included'
 when is_direct or is_family then 'review_prior_label'
 else 'review_secondary'
end resolution,
case when lexical_cluster is not null then lexical_cluster when is_direct or is_family then prior_cluster else secondary end cluster
from flags
""", [exclude])
c.execute(f"""
create temp table p07_matched_observations as
select o.* exclude(raw_cells), s.nominal_domain, lower(regexp_extract(o.target_url,'{matcher}',1)) landing_host
from corpus.query_observation_keys o join candidates c using(query_id) join corpus.sources s using(source_id)
""")

def out(file,sql,kind='csv'):
    path = str((args.out / (file+'.'+kind)).resolve()).replace(chr(39), chr(39)*2)
    c.execute(f"copy ({sql}) to '{path}' (format {kind}{', header true' if kind=='csv' else ', compression zstd'})")

out('queries_pending', '''select c.*,q.query_raw,q.search_market,q.search_engine,q.volume,q.cpc,q.kd,q.volume_metric,q.target_url,q.observation_count,q.unknown_scope
from candidates c join corpus.queries q using(query_id) order by resolution,cluster,volume desc nulls last''')
out('observations_pending','from p07_matched_observations','parquet')
out('sites_pending','''select coalesce(nullif(o.nominal_domain,''),nullif(o.landing_host,''),'(unknown)') domain,
 string_agg(distinct o.source_region,'|' order by o.source_region) folders,
 count(distinct o.query_id) candidates,count(distinct o.query_id) filter(where c.resolution='rule_included') contextual,
 count(distinct o.target_url) pages,count(distinct o.source_id) files,
 string_agg(distinct c.cluster,'|' order by c.cluster) families
 from p07_matched_observations o join candidates c using(query_id) group by all order by contextual desc,candidates desc''')
out('top_urls_pending','''select o.nominal_domain, o.landing_host,o.target_url,count(distinct o.query_id) candidates,
count(distinct o.query_id) filter(where c.resolution='rule_included') contextual,
max(o.volume) max_observed_volume,arg_max(o.query_raw,coalesce(o.volume,0)) example,
string_agg(distinct c.cluster,'|' order by c.cluster) families from p07_matched_observations o join candidates c using(query_id)
where o.target_url is not null and o.target_url<>'' group by all order by contextual desc,candidates desc''')
out('source_inventory', '''select s.source_id,s.region,s.title,s.source_url,s.export_date,s.nominal_domain,s.status,s.query_rows,s.incomplete_filename,s.sha256,
count(o.query_id) candidate_observations,count(distinct o.query_id) candidate_keys
from corpus.sources s left join p07_matched_observations o using(source_id)
where s.status in ('processed','partial_schema') group by all order by s.region,s.title''')
meta={key:c.execute(sql).fetchone()[0] for key,sql in {
    'corpus_keys':'select count(*) from corpus.queries',
    'corpus_observations':'select count(*) from corpus.query_observation_keys',
    'scanned_files':"select count(*) from corpus.sources where status in ('processed','partial_schema')",
    'source_folders':"select count(distinct region) from corpus.sources where status in ('processed','partial_schema')",
    'candidates':'select count(*) from candidates',
    'candidate_observations':'select count(*) from temp.main.p07_matched_observations',
    'v4_direct':'select count(*) from candidates where is_direct',
}.items()}
(args.out/'base.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print(meta,flush=True)
print(c.execute('select resolution, cluster,count(*) n from candidates group by all order by 1,n desc').fetchall(),flush=True)
