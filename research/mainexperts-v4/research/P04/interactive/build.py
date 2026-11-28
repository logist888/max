"""Build an offline P04 research explorer from the approved evidence package."""
import argparse
import base64
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("release", type=Path, help="Directory containing data/ and screenshots/")
p.add_argument("output", type=Path, help="Output HTML file")
a = p.parse_args()
ROOT = a.release.resolve()
DATA = ROOT / "data"

def rows(name):
    with (DATA / (name + ".csv")).open(encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)

def table(records, spec):
    field_map = [(alias, name.rstrip("#"), name.endswith("#")) for item in spec.split() for alias, name in (item.split(":", 1),)]
    packed = []
    for record in records:
        row = []
        for _, name, numeric in field_map:
            val = record[name]
            row.append(float(val) if numeric and val else None if numeric else val)
        packed.append(row)
    return [[alias for alias, _, _ in field_map], packed]

landing_rows = list(rows("landings"))
proj_for_landing = {
    (l["nominal_domain"], l["landing_host"], l["target_url"]): l["PROJECT_ID"]
    for l in landing_rows
}
obs_rows = []
for o in rows("observations"):
    o["project"] = proj_for_landing[(o["nominal_domain"], o["landing_host"], o["target_url"])]
    obs_rows.append(o)

source_rows = list(rows("source_coverage"))
shot_rows = list(rows("screenshots"))
coverage = json.loads((DATA / "coverage.json").read_text(encoding="utf-8"))
data = {
    "coverage": coverage,
    "projects": table(rows("projects"), """
        id:PROJECT_ID domain:DOMAIN name:NAME status:STATUS files:SOURCE_FILES# folders:SOURCE_FOLDERS
        observations:OBSERVATIONS# keys:QUERY_KEYS# domains:SOURCE_DOMAINS landings:P04_LANDING_URLS#
        routes:ROUTES# shots:SCREENSHOTS#
    """),
    "queries": table(rows("queries"), """
        id:QUERY_ID raw:QUERY_RAW normalized:QUERY_NORMALIZED language:LANGUAGE market:SEARCH_MARKET
        engine:SEARCH_ENGINE region:SOURCE_REGION goal:DESTINATION volume:VOLUME# metric:VOLUME_METRIC
        cluster:CLUSTER_BASE_ID subcluster:CLUSTER_ID task:TASK_ID intent:INTENT_ID level:EVIDENCE_LEVEL
        reason:REASON source:SOURCE_ID date:OBSERVED_DATE
    """),
    "observations": table(obs_rows, """
        id:observation_id query:query_id project:project raw:query_raw source:source_id
        sheet:sheet row:row_no# market:search_market engine:search_engine folder:source_region
        target:target_url volume:volume# metric:volume_metric cpc:cpc# kd:kd# position:position# date:observed_date
    """),
    "routes": table(rows("pathways"), """
        id:PATH_ID project:PROJECT_ID domain:DOMAIN name:PROJECT_NAME region:REGION scope:SCOPE
        clusters:CLUSTERS_HINT entry:ENTRY_URL final:FINAL_URL cta:CTA_NATIVE translation:CTA_RU
        access:ACCESS_OR_INPUTS free:FREE_OUTCOME paid:PAID_PRODUCT price:PRICE provider:PUBLIC_PROVIDER
        recipient:VERIFIED_PAYMENT_RECIPIENT outcome:MONETIZATION verification:VERIFICATION
        sources:EVIDENCE_URLS limits:LIMITS frames:SCREENSHOT_IDS
    """),
    "steps": table(rows("steps"), """
        route:PATH_ID id:STEP_ID number:STEP_NO url:URL element:ELEMENT cta:CTA_NATIVE next:NEXT_ACTION
        outcome:OUTCOME price:PRICE provider:PUBLIC_PROVIDER source:EVIDENCE_URL check:VERIFICATION
    """),
    "shots": table(shot_rows, """
        id:SCREENSHOT_ID route:PATH_ID step:STEP_ID url:URL date:CAPTURED_AT language:LOCALE
        device:DEVICE state:STATE size:PIXELS proof:PROVES
    """),
    "routeObservations": table(rows("path_observations"), """
        route:PATH_ID observation:OBSERVATION_ID query:QUERY_ID project:PROJECT_ID match:MATCH_BASIS
    """),
    "shotLinks": table(rows("screenshot_links"), "shot:SCREENSHOT_ID route:PATH_ID step:STEP_ID"),
    "sources": table(source_rows, """
        id:source_id region:region name:title domain:nominal_domain url:source_url status:status
        rows:query_rows# included:included_observations# keys:included_keys# incomplete:incomplete_filename
    """),
    "landings": table(landing_rows, """
        project:PROJECT_ID domain:nominal_domain url:target_url regions:source_regions
        keys:included_keys# roles:families role:PAGE_ROLE roleNote:PAGE_ROLE_BASIS
        status:PUBLIC_CHECK now:VERIFIED_CURRENT_URL title:PUBLIC_TITLE note:PUBLIC_PROBE_NOTE
    """),
}
def size(key):
    return len(data[key][1])
assert size("queries") == coverage["candidate_counts"]["included"]
assert size("observations") == coverage["included_observations"]
assert size("routes") == coverage["paths"]
assert size("steps") == coverage["steps"]
assert size("shots") == coverage["screenshots"]
assert size("sources") == coverage["v4_source_files"]
queries = {r[0] for r in data["queries"][1]}
observations = {r[0] for r in data["observations"][1]}
routes = {r[0] for r in data["routes"][1]}
shots = {r[0] for r in data["shots"][1]}
assert all(r[1] in queries for r in data["observations"][1])
assert all(r[0] in routes and r[1] in observations and r[2] in queries for r in data["routeObservations"][1])
assert all(r[0] in shots and r[1] in routes for r in data["shotLinks"][1])

def payload():
    # HTML raw-text elements must never contain a literal closing script sequence from source data.
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

def screenshots():
    for r in shot_rows:
        ident = r["SCREENSHOT_ID"]
        if not all(ch.isalnum() or ch in "-_." for ch in ident):
            raise ValueError(f"Invalid screenshot ID {ident}")
        f = ROOT / r["HTML_JPEG"]
        raw = f.read_bytes()
        assert raw.startswith(b"\xff\xd8") and raw.endswith(b"\xff\xd9"), f
        yield f'<script type="application/octet-stream" id="asset-{ident}">{base64.b64encode(raw).decode("ascii")}</script>'

doc = (HERE / "index.html").read_text(encoding="utf-8")
parts = doc.split("<!-- ASSETS -->")
assert len(parts) == 2
prefix = parts[0].replace("/* CSS */", (HERE / "style.css").read_text(encoding="utf-8"))
prefix = prefix.replace("<!-- DATA -->", payload())
suffix = parts[1].replace("/* SCRIPT */", (HERE / "app.js").read_text(encoding="utf-8"))
a.output.parent.mkdir(parents=True, exist_ok=True)
with a.output.open("w", encoding="utf-8", newline="\n") as out:
    out.write(prefix)
    for image in screenshots():
        out.write(image + "\n")
    out.write(suffix)
print(a.output, a.output.stat().st_size, {k: size(k) for k in data if k != "coverage"})
