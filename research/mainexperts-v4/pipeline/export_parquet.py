"""Publish portable Parquet tables and reconstruct a relational database from them."""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

import duckdb

from warehouse import OBSERVATION_VIEWS, quote_path

TABLES = ("sources","source_sheets","queries","query_labels","tasks","elements","services","products","conversions",
          "cluster_catalog","gap_register","gap_sources","regions_ontology","regional_documents","objectives_ontology",
          "commercial_benchmarks","cta_localizations","conversion_intents","markets_language","neutral_conversions","neutral_cta_localizations","query_translations","commercial_review")
PART_MAX = 178 * 1024**2
BASE = Path(__file__).resolve().parent

def archive_pairs(destination, files):
    with zipfile.ZipFile(destination,"w",compression=zipfile.ZIP_STORED,allowZip64=True) as out:
        for path, name in files:
            out.write(path,name)
    return {"file":destination.name,"bytes":destination.stat().st_size,
            "sha256":hashlib.file_digest(destination.open("rb"),"sha256").hexdigest()}

def observation_archives(stage, output):
    sources=json.loads((stage/"sources.json").read_text())
    eligible = [s for s in sources if (stage/(s["id"]+".parquet")).is_file()]
    groups=[]; current=[]; n=0
    for s in sorted(eligible,key=lambda z:(z["region"],z["id"])):
        p=stage/(s["id"]+".parquet")
        size=p.stat().st_size
        if current and n+size>PART_MAX:
            groups.append(current); current=[]; n=0
        current.append((p,"observations/"+p.name))
        n+=size
    if current:
        groups.append(current)
    return [archive_pairs(output/f"mainexperts-v4-observations-{idx:02d}.zip",g)
            for idx,g in enumerate(groups,1)]

def pack_core(db, stage, output):
    c=duckdb.connect(str(db),read_only=True)
    c.execute("set threads=6; set memory_limit='2GB';")
    directory=output.parent/"parquet-core"
    directory.mkdir(exist_ok=True)
    counts={}
    present={r[0] for r in c.execute("show tables").fetchall()}
    for name in TABLES:
        if name not in present:
            continue
        out=directory/(name+".parquet")
        c.execute(f"copy {name} to {quote_path(out)} (format parquet, compression zstd, row_group_size 65000)")
        counts[name]=c.execute(f"select count(*) from {name}").fetchone()[0]
    readme=directory/"README.txt"
    readme.write_text("MainExperts v4.0: parquet relations. Extract all observation and core archives into the same directory. See 08-pipeline.md and use export_parquet.py restore. Source query corpus remains private.\n")
    shards=[]
    for tag,paths in (
        ("queries",[directory/"queries.parquet"]),
        ("labels",[directory/"query_labels.parquet"]),
        ("catalog",[p for p in directory.glob("*") if p.name not in {"queries.parquet","query_labels.parquet"}]+[stage/"sources.json"]),
    ):
        shards.append(archive_pairs(output/f"mainexperts-v4-{tag}.zip",[(p,"tables/"+p.name) for p in paths]))
    return counts,shards

def restore(directory, db):
    c=duckdb.connect(str(db))
    c.execute("set threads=6; set memory_limit='3GB'; set preserve_insertion_order=false;")
    for name in TABLES:
        path=directory/"tables"/(name+".parquet")
        if path.exists():
            c.execute(f"create or replace table {name} as select * from read_parquet({quote_path(path)})")
    pattern=directory/"observations"/"*.parquet"
    c.execute(f"create or replace table observations as select * from read_parquet({quote_path(pattern)},union_by_name=true)")
    from warehouse import repair_duplicate_provenance
    repair_duplicate_provenance(c)
    c.execute(OBSERVATION_VIEWS.split("create or replace table queries as")[0])
    c.execute((BASE/"matrix.sql").read_text())
    assert c.execute("select count(*) from queries").fetchone()==c.execute("select count(*) from query_journey").fetchone()
    print("Warehouse restored",db)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=["observations","pack","restore"])
    p.add_argument("--db",type=Path,required=True)
    p.add_argument("--stage",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.mode=="restore":
        restore(a.output,a.db)
        return
    a.output.mkdir(parents=True,exist_ok=True)
    path=a.output/"parquet-manifest.json"
    manifest=json.loads(path.read_text()) if path.exists() else {}
    if a.mode=="observations":
        manifest["observations"]=observation_archives(a.stage,a.output)
    if a.mode=="pack":
        manifest["table_counts"],manifest["core"]=pack_core(a.db,a.stage,a.output)
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(json.dumps(manifest,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
