"""Identify ranking landings from all observations and queue URLs for a public read."""
import argparse
from pathlib import Path

import duckdb

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("workspace", type=Path)
p.add_argument("--queue", action="store_true")
a = p.parse_args()
work = a.workspace.resolve()
data = work / "data"
db = duckdb.connect()
db.read_parquet(str(data / "observations_pending.parquet")).create_view("observations")
if a.queue:
    db.read_csv(str(work / "review_labels.csv"), header=True, all_varchar=True).create_view("review")
    db.sql("""select nominal_domain, landing_host, target_url, count(distinct query_id) candidates,
        count(distinct query_id) contextual, max(volume) max_observed_volume,
        arg_max(query_raw, coalesce(volume,0)) example, string_agg(distinct cluster,'|' order by cluster) families
        from observations join review using(query_id)
        where decision='accept' and target_url is not null and target_url<>''
        group by all order by contextual desc,candidates desc""").write_csv(str(data / "top_urls_accepted.csv"), header=True)
else:
    ranking = r"(?i)(?:/(?:[^/?#]*/)*(?:ranking|rankings|league-table|league-tables|clasifica(?:ci[oó]n)?|classement|classifica|palmares|rating|reyting|reiting)(?:[-_/]|[?#]|$)|/[^/?#]*[-_](?:ranking|rankings|classement|classifica|reyting|reiting)(?:[-_/]|[?#]|$)|https?://(?:www\.)?(?:edurank\.org|unirank\.org|shanghairanking\.com)(?:/|$))"
    keys = db.execute("select distinct query_id from observations where regexp_matches(coalesce(target_url,''),?) order by query_id", [ranking]).fetchall()
    (data / "ranking-keys.txt").write_text("".join(key + "\n" for (key,) in keys))
