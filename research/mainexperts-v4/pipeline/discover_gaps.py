"""Reverse-map unclassified queries using independent page and modifier cues."""
import argparse
from pathlib import Path

import duckdb

from warehouse import quote_path

TERMS = (
  ("admissions",r"/(admission|admissions|apply|applications|bewerb|zulassung|iscrizion|immatricolaz|ingreso|inscrip|abitur|postuplen|прием|поступ|jupas|ucas)"),
  ("funding",r"/(financial-aid|financialaid|funding|scholarship|bourses|stipend|bolsas|becas|grants|funds|aid)"),
  ("credit-recognition",r"/(recognition|equivalence|equivalency|anerkennung|credential|transfer|credit|reconnaissance)"),
  ("program-search",r"/(programs|programmes|undergraduate|postgraduate|degrees|studieng[aä]ng|formation|educational-program|universit|colleges|specialit|специальност)"),
  ("external-visa",r"/(visa|immigration|student-pass|study-permit|aufenthalt|soggiorno|visado)"),
)
MODS = r"(?i)(review service|application check|essay review|coaching|counseling|[ -]berater|nachhilfe|prix|consulenza|asesoria|asesor[ií]a|revisi[oó]n|платн|репетитор|сопровожден|консультант|под ключ|付费|收费|收費|升學顧問|润色|潤色|مستشار)"
def copy(c, sql, out):
    c.execute(f"copy ({sql}) to {quote_path(out)} (format csv,header true,force_quote *)")

def main():
    a=argparse.ArgumentParser(description=__doc__); a.add_argument("--db",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True); p=a.parse_args()
    c=duckdb.connect(str(p.db),read_only=True); c.execute("set threads=7; set memory_limit='2GB';")
    buckets="case "+" ".join(f"when regexp_matches(coalesce(target_url,''),'{exp}') then '{name}'" for name,exp in TERMS)+" end"
    c.execute(f"""create or replace temporary view unclassified_scope as
        select query_id, query_raw,query_normalized, coalesce(search_market,'?') search_market,
          search_engine, language, source_id, source_url, target_url, volume, volume_metric,
          {buckets} as page_candidate,
          regexp_matches(query_raw,'{MODS}') as modifier_candidate
        from query_journey where cluster_id is null and relevance='unresolved'""")
    copy(c,"""select search_market,language,page_candidate, count(*) unresolved,
      count(*) filter (where modifier_candidate) as with_commercial_modifier
      from unclassified_scope group by all order by unresolved desc""",p.output/"reverse_gap_counts.csv")
    copy(c,"""select * exclude(row_rank) from (
      select *,row_number() over(partition by search_market,page_candidate,modifier_candidate
        order by volume desc nulls last,query_id) as row_rank from unclassified_scope
      where (page_candidate is not null or modifier_candidate)
        and search_market in ('?','RU','GB','US','CA','CH','FR','IT','ES','AE','SG','HK','CN','DE','AU')
      ) where row_rank<=6 order by 4,12,13 desc,volume desc nulls last""",p.output/"reverse_gap_examples.csv")
    copy(c,"""with tokens as (
      select search_market, language, page_candidate, source_id,
        unnest(list_distinct(regexp_extract_all(query_normalized,'[\\p{L}][\\p{L}-]{3,}'))) token
      from unclassified_scope where page_candidate is not null
    ), totals as (
      select search_market,language,page_candidate,token,count(*) pairs,count(distinct source_id) sources
      from tokens group by all having sources>=2
    ) select * from totals
    qualify row_number() over(partition by search_market,language,page_candidate
                     order by pairs desc,token)<=12 order by search_market,language,page_candidate,pairs desc
    """,p.output/"reverse_gap_lexemes.csv")
if __name__=="__main__":
    main()
