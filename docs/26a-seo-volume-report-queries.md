# Приложение к отчёту об объёме SEO-страниц: запросы и скрипты

Приложение к `docs/26-seo-volume-report.md` (13.11.2026). Каждое число отчёта воспроизводится запросом из этого файла.

## 8. Запросы

Выгрузки выполнялись через `q.py`: строка подключения читается из `.env.preview` и не печатается, а сессия получает `SET SESSION TRANSACTION READ ONLY`. `PORTAL_DB_URL` — схема `portal`, `PORTAL_MAIN_DB_URL` — `me_dev1`. Затем `load.py` грузит TSV в SQLite, `analysis.py` создаёт временные таблицы и выполняет агрегаты.

### 8.1 Портал (MariaDB, схема `portal`)

```sql
-- E0 documents by kind: all, listed (crates/portal-db/src/listed.rs), merged
SELECT kind, count(*) AS docs,
  sum(state = 'active' AND hidden = 0 AND merged_into IS NULL AND slug IS NOT NULL AND country_code <> 'XX') AS listed,
  sum(merged_into IS NOT NULL) AS merged, sum(variant_of IS NOT NULL) AS variants
FROM doc GROUP BY kind;
SHOW TABLES LIKE '%locale%';
SHOW TABLES LIKE '%market%';
SHOW TABLES LIKE '%transl%';
SHOW TABLES LIKE '%entry%';

-- E1 programs: every listed programme (crates/portal-db/src/listed.rs: active, not hidden, not merged, slug, known country)
SELECT d.id, d.country_code AS cc, d.city, d.level AS lvl, (d.variant_of IS NOT NULL) AS is_var,
  CONCAT(d.owner_source_id, '|', d.owner_ext_id) AS inst,
  LEFT(JSON_VALUE(d.body, '$.direction.code'), 5) AS dir,
  JSON_VALUE(d.body, '$.study_form') AS form,
  JSON_VALUE(d.body, '$.price_per_year.amount') AS amt,
  JSON_VALUE(d.body, '$.price_per_year.currency') AS cur,
  JSON_VALUE(d.body, '$.price_per_year.audience') AS aud,
  JSON_VALUE(d.body, '$.places_budget') AS pb,
  JSON_VALUE(d.body, '$.for_foreigners') AS foreigners,
  COALESCE(JSON_QUERY(d.body, '$.languages'), '[]') AS langs,
  COALESCE(JSON_EXTRACT(d.body, '$.deadlines[*].closes'), '[]') AS dl_closes,
  COALESCE(JSON_EXTRACT(d.body, '$.deadlines[*].year'), '[]') AS dl_years,
  COALESCE(JSON_EXTRACT(d.body, '$.starts[*].year'), '[]') AS st_years,
  (JSON_SEARCH(d.body, 'one', 'eu', NULL, '$.prices[*].audience') IS NOT NULL) AS has_eu
FROM doc d
WHERE d.kind = 'program' AND d.state = 'active' AND d.hidden = 0 AND d.merged_into IS NULL
  AND d.slug IS NOT NULL AND d.country_code <> 'XX';

-- E2 institutions: every document of kind institution; listed = crates/portal-db/src/listed.rs
SELECT d.id, CONCAT(d.source_id, '|', d.source_ext_id) AS ikey, d.country_code AS cc, d.city, d.category,
  (d.state = 'active' AND d.hidden = 0 AND d.merged_into IS NULL AND d.slug IS NOT NULL AND d.country_code <> 'XX') AS listed,
  (d.merged_into IS NOT NULL) AS merged,
  (JSON_VALUE(d.body, '$.names.full') IS NOT NULL) AS has_name,
  (JSON_VALUE(d.body, '$.website') IS NOT NULL) AS has_site,
  (JSON_VALUE(d.body, '$.address') IS NOT NULL OR JSON_VALUE(d.body, '$.phone') IS NOT NULL OR JSON_VALUE(d.body, '$.email') IS NOT NULL) AS has_contact,
  (JSON_VALUE(d.body, '$.funding') IS NOT NULL OR JSON_VALUE(d.body, '$.founded_year') IS NOT NULL OR JSON_VALUE(d.body, '$.attrs.institution_type') IS NOT NULL) AS has_type,
  (JSON_VALUE(d.body, '$.coordinates.lat') IS NOT NULL) AS has_coords,
  (JSON_VALUE(d.body, '$.price_from.amount') IS NOT NULL) AS has_price,
  JSON_VALUE(d.body, '$.programs_count') AS programs_count
FROM doc d WHERE d.kind = 'institution';

-- E3 cities
-- E3 cities: every document of kind city with the counts the projection stores (crates/portal-sync/src/geo.rs)
SELECT d.id, d.country_code AS cc, d.city,
  (d.state = 'active' AND d.hidden = 0 AND d.merged_into IS NULL AND d.slug IS NOT NULL AND d.country_code <> 'XX') AS listed,
  JSON_VALUE(d.body, '$.counts.programs') AS n_prog, JSON_VALUE(d.body, '$.counts.universities') AS n_univ,
  JSON_VALUE(d.body, '$.counts.colleges') AS n_coll
FROM doc d WHERE d.kind = 'city';

-- E4 directions
-- E4 directions (CIP series 2, family 4, code 6); a page exists for a family with a slug (field_page/mod.rs:237)
SELECT d.id, JSON_VALUE(d.body, '$.code') AS code, JSON_VALUE(d.body, '$.level') AS lvl,
  (d.slug IS NOT NULL AND d.state = 'active' AND d.hidden = 0 AND d.merged_into IS NULL) AS has_page,
  JSON_VALUE(d.body, '$.sphere.source_ext_id') AS sphere
FROM doc d WHERE d.kind = 'direction';

-- E5 professions
-- E5 professions and the directions they link to (body.directions[].code)
SELECT d.id, (d.slug IS NOT NULL AND d.state = 'active' AND d.hidden = 0 AND d.merged_into IS NULL) AS has_page,
  COALESCE(JSON_EXTRACT(d.body, '$.directions[*].code'), '[]') AS dirs
FROM doc d WHERE d.kind = 'profession';

-- E6 countries
-- E6 countries: page, editorial texts (body.editorial.texts), Russian cases (body.editorial.cases)
SELECT d.country_code AS cc, (d.slug IS NOT NULL) AS has_page,
  COALESCE(CHAR_LENGTH(JSON_QUERY(d.body, '$.editorial.texts.en')), 0) AS ed_en_chars,
  COALESCE(CHAR_LENGTH(JSON_QUERY(d.body, '$.editorial.texts.ru')), 0) AS ed_ru_chars,
  (JSON_VALUE(d.body, '$.editorial.cases.prepositional') IS NOT NULL) AS has_prep
FROM doc d WHERE d.kind = 'country';

-- E7 spheres
-- E7 spheres with the counts the projection stores
SELECT d.id, d.slug, JSON_VALUE(d.body, '$.programs') AS n_prog, JSON_VALUE(d.body, '$.institutions') AS n_inst,
  JSON_VALUE(d.body, '$.directions') AS n_dir
FROM doc d WHERE d.kind = 'sphere';

-- E8 currency rates
-- E8 rates: units of the currency per one USD (fx_rate, ExchangeRate-API)
SELECT currency, per_usd, as_of FROM fx_rate;

-- E9 AI texts
-- E9 AI and editorial texts a visitor can meet: ai_block rows by kind, section, language, state
SELECT kind, source_id, source_ext_id, section, lang, country, state, CHAR_LENGTH(body) AS chars FROM ai_block;

-- E10 sitemap, waves, site pages, country page counts
SELECT name, lang, kind, country, urls, built_at FROM sitemap_file;
SELECT count(*) AS seo_waves FROM seo_wave;
SELECT count(*) AS site_pages, sum(noindex) AS noindex_pages, sum(route LIKE '%{%') AS templated FROM site_page;
SELECT d.country_code, JSON_VALUE(d.body, '$.counts.programs') AS page_programs FROM doc d WHERE d.kind = 'country' ORDER BY 1;

-- E11 AI texts (>= 300 chars) mapped to listed docs by (kind, source_id, source_ext_id)
SELECT a.kind, a.section, a.state, d.kind AS doc_kind, d.state AS doc_state, d.hidden, d.merged_into IS NULL AS not_merged,
  d.slug IS NOT NULL AS has_slug, d.variant_of IS NOT NULL AS is_variant, d.country_code,
  JSON_VALUE(d.body, '$.price_per_year.amount') IS NOT NULL AS has_price, CHAR_LENGTH(a.body) AS chars
FROM ai_block a LEFT JOIN doc d ON d.kind = a.kind AND d.source_id = a.source_id AND d.source_ext_id = a.source_ext_id
WHERE a.kind IN ('program', 'profession', 'country', 'city', 'direction', 'institution') AND a.section IN ('about', 'seo_text', 'study', 'become')
ORDER BY a.kind, a.section;

-- E12 the programmes with an AI description: future deadline, price
SELECT d.id, d.country_code, d.variant_of IS NOT NULL AS is_variant,
  JSON_VALUE(d.body, '$.price_per_year.amount') IS NOT NULL AS has_price,
  (SELECT count(*) FROM JSON_TABLE(d.body, '$.deadlines[*]' COLUMNS (closes VARCHAR(40) PATH '$.closes')) t WHERE t.closes >= '2026-11-13') AS future_deadlines
FROM doc d WHERE d.kind = 'program' AND (d.source_id, d.source_ext_id) IN
  (SELECT source_id, source_ext_id FROM ai_block WHERE kind = 'program' AND section = 'about');

-- E13 server version, site languages, markets, content tables
SELECT VERSION() AS server_version;
SELECT code, enabled, indexable, is_default FROM site_language ORDER BY code;
SELECT country, currency, active FROM site_market ORDER BY position;
SELECT (SELECT count(*) FROM tr_translation) AS tr_translation_rows, (SELECT count(*) FROM entry) AS entry_rows,
  (SELECT count(*) FROM seo_wave) AS seo_wave_rows, (SELECT count(*) FROM field_override) AS field_override_rows;

-- E14 name fields of the documents with a page: Russian name, short name, Russian cases (editorial.cases.*)
SELECT kind, count(*) AS docs,
  sum(JSON_EXISTS(body, '$.names.ru') OR JSON_EXISTS(body, '$.names.by_lang.ru')) AS with_name_ru,
  sum(JSON_VALUE(body, '$.names.short') IS NOT NULL) AS with_name_short,
  sum(JSON_EXISTS(body, '$.editorial.cases')) AS with_ru_cases
FROM doc WHERE slug IS NOT NULL AND state = 'active' AND hidden = 0 AND merged_into IS NULL GROUP BY kind;

-- E15 why programme documents have no page: state, hidden, slug, country; RU and JP separately
SELECT IF(country_code IN ('RU', 'JP'), country_code, 'other') AS cc, state, hidden, slug IS NULL AS no_slug,
  country_code = 'XX' AS cc_xx, count(*) n
FROM doc WHERE kind = 'program' GROUP BY 1, 2, 3, 4, 5 ORDER BY n DESC;
```

### 8.2 Источник (MariaDB, `me_dev1`)

```sql
-- M1 institutions of the source by category (education_institution)
SELECT category, count(*) n, sum(merged_into_id IS NULL) not_merged, sum(age_min IS NOT NULL OR age_max IS NOT NULL) with_age,
  sum(lat IS NOT NULL) with_coords, sum(visa_sponsor IS NOT NULL) with_visa_sponsor, sum(boarding IS NOT NULL) with_boarding
FROM education_institution GROUP BY category;
-- M2 programmes of the source by course kind and institution category
SELECT COALESCE(course_kind, '(none)') ck, COALESCE(inst_category, '(none)') ic, count(*) n,
  sum(age_min IS NOT NULL OR age_max IS NOT NULL) with_age, sum(cost_year IS NOT NULL) with_price
FROM education_program GROUP BY ck, ic ORDER BY n DESC;
-- M3 sessions (start dates) of short/language/summer/school programmes
SELECT COALESCE(p.course_kind, '(none)') ck, COALESCE(p.inst_category, '(none)') ic, count(DISTINCT s.program_id) progs_with_session,
  count(DISTINCT CASE WHEN s.starts_on IS NOT NULL OR s.start_month IS NOT NULL THEN s.program_id END) with_start,
  count(DISTINCT CASE WHEN s.starts_on >= '2026-11-13' THEN s.program_id END) with_future_start,
  count(DISTINCT CASE WHEN s.age_min IS NOT NULL OR s.age_max IS NOT NULL THEN s.program_id END) with_session_age,
  count(DISTINCT CASE WHEN s.amount IS NOT NULL THEN s.program_id END) with_session_price
FROM education_session s JOIN education_program p ON p.id = s.program_id
GROUP BY ck, ic ORDER BY progs_with_session DESC;
-- M4 deadlines by scope (country calendar = scope 'country')
SELECT scope, count(*) n, count(DISTINCT country_iso) countries, min(campaign_year) y_min, max(campaign_year) y_max FROM education_deadline GROUP BY scope;
SELECT campaign_year, count(DISTINCT country_iso) countries, count(*) n FROM education_deadline WHERE scope = 'country' GROUP BY campaign_year;
-- M5 prices by audience (price for a citizenship group)
SELECT audience, count(*) n, count(DISTINCT country_iso) countries FROM education_program_price GROUP BY audience;
-- M6 country geo dictionary
SELECT kind, count(*) FROM corpus_geo GROUP BY kind;

-- M7 future deadlines of the country and institution scopes (not projected: source.rs:279 reads scope 'programme' only)
SELECT scope, country_iso, count(*) n, count(DISTINCT institution_id) insts, min(campaign_year) y_min, max(campaign_year) y_max
FROM education_deadline
WHERE scope IN ('country', 'institution') AND ends_at >= '2026-11-13' AND audience IN ('', 'international')
  AND stage IN ('applications', 'equal_consideration', 'application_deadline', 'selective_courses')
GROUP BY scope, country_iso ORDER BY scope, country_iso;
-- M8 any country-scope rows regardless of stage and audience, by year
SELECT country_iso, campaign_year, count(*) n, max(ends_at) last_close, GROUP_CONCAT(DISTINCT stage) stages, GROUP_CONCAT(DISTINCT audience) audiences
FROM education_deadline WHERE scope = 'country' GROUP BY country_iso, campaign_year ORDER BY country_iso, campaign_year;

-- M7b institutions with a future institution-scope deadline (668 rows)
SELECT DISTINCT institution_id FROM education_deadline WHERE scope = 'institution' AND ends_at >= '2026-11-13' AND audience IN ('', 'international') AND stage IN ('applications', 'equal_consideration', 'application_deadline', 'selective_courses');

-- M9 source programmes by country: how many countries, and the programmes of countries without programmes in the portal index
SELECT count(DISTINCT country_iso) AS countries, count(*) AS programs FROM education_program;
SELECT country_iso, count(*) n FROM education_program
WHERE country_iso NOT IN ('AE','AU','CA','CN','CZ','DE','DK','ES','FI','FR','GB','HU','IE','IT','KR','KZ','NL','NO','PL','SE','SG','TR','US')
GROUP BY country_iso ORDER BY n DESC LIMIT 15;
```

### 8.3 Загрузка в SQLite (`load.py`)

```python
"""Load the TSV extracts (MariaDB SELECTs in e*.sql/extract.sql) into SQLite: load.py <dir>."""
import csv, json, sqlite3, sys
from pathlib import Path

D = Path(sys.argv[1])
TODAY = "2026-11-13"
TAUGHT_IN_ENGLISH = {"AU", "GB", "IE", "NZ", "US"}  # crates/portal-search/src/build.rs:163
db = sqlite3.connect(D / "portal.sqlite")
csv.field_size_limit(10**9)


def rows(name):
    with open(D / f"{name}.tsv", encoding="utf-8") as f:
        r = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        head = next(r)
        for row in r:
            yield dict(zip(head, [None if v == "NULL" else v for v in row]))


def arr(v):
    return json.loads(v) if v else []


def num(v):
    return float(v) if v not in (None, "") else None


db.executescript("""
DROP TABLE IF EXISTS fx; DROP TABLE IF EXISTS p; DROP TABLE IF EXISTS plang; DROP TABLE IF EXISTS pyear;
DROP TABLE IF EXISTS inst; DROP TABLE IF EXISTS city; DROP TABLE IF EXISTS dirs; DROP TABLE IF EXISTS prof;
DROP TABLE IF EXISTS profdir; DROP TABLE IF EXISTS country; DROP TABLE IF EXISTS sphere; DROP TABLE IF EXISTS ai;
CREATE TABLE fx(currency TEXT PRIMARY KEY, per_usd REAL);
CREATE TABLE p(id INTEGER PRIMARY KEY, cc TEXT, city TEXT, lvl TEXT, is_var INT, inst TEXT, dir TEXT, form TEXT,
  priced INT, usd REAL, free INT, fdl INT, eu INT, own_lang INT);
CREATE TABLE plang(id INT, lang TEXT);
CREATE TABLE pyear(id INT, year INT);
CREATE TABLE inst(id INT, ikey TEXT, cc TEXT, city TEXT, category TEXT, listed INT, merged INT, has_name INT, has_site INT,
  has_contact INT, has_type INT, has_coords INT, has_price INT, programs_count INT);
CREATE TABLE city(id INT, cc TEXT, city TEXT, listed INT, n_prog INT, n_univ INT, n_coll INT);
CREATE TABLE dirs(id INT, code TEXT, lvl INT, has_page INT, sphere TEXT);
CREATE TABLE prof(id INT, has_page INT);
CREATE TABLE profdir(prof INT, code TEXT);
CREATE TABLE country(cc TEXT, has_page INT, ed_en INT, ed_ru INT, has_prep INT);
CREATE TABLE sphere(id INT, slug TEXT, n_prog INT, n_inst INT, n_dir INT);
CREATE TABLE ai(kind TEXT, ext TEXT, section TEXT, lang TEXT, country TEXT, state TEXT, chars INT);
""")
fx = {r["currency"]: float(r["per_usd"]) for r in rows("e8_fx")}
db.executemany("INSERT INTO fx VALUES(?,?)", fx.items())

P, L, Y = [], [], []
for r in rows("extract"):
    amt = num(r["amt"])
    # crates/portal-search/src/build.rs:371-381: zero without an audience is no price; free = priced 0.
    priced = amt is not None and not (amt == 0 and r["aud"] is None)
    free_price = priced and amt == 0
    pb = num(r["pb"])
    free = (pb > 0 or free_price) if pb is not None else free_price
    usd = amt / fx[r["cur"]] if priced and r["cur"] in fx else None
    fdl = any(c >= TODAY for c in arr(r["dl_closes"]) if c)
    own = arr(r["langs"])
    langs = own or (["en"] if r["cc"] in TAUGHT_IN_ENGLISH else [])
    P.append((int(r["id"]), r["cc"], r["city"], r["lvl"], int(r["is_var"]), r["inst"], r["dir"], r["form"],
              int(priced), usd, int(free), int(fdl), int(r["has_eu"]), int(bool(own))))
    L += [(int(r["id"]), x) for x in set(langs)]
    Y += [(int(r["id"]), y) for y in set(arr(r["dl_years"]) + arr(r["st_years"])) if y]
db.executemany("INSERT INTO p VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", P)
db.executemany("INSERT INTO plang VALUES(?,?)", L)
db.executemany("INSERT INTO pyear VALUES(?,?)", Y)

cols = "id ikey cc city category listed merged has_name has_site has_contact has_type has_coords has_price programs_count".split()
db.executemany(f"INSERT INTO inst VALUES({','.join('?' * len(cols))})", ([r[c] for c in cols] for r in rows("e2_inst")))
cols = "id cc city listed n_prog n_univ n_coll".split()
db.executemany("INSERT INTO city VALUES(?,?,?,?,?,?,?)", ([r[c] for c in cols] for r in rows("e3_city")))
db.executemany("INSERT INTO dirs VALUES(?,?,?,?,?)", ((r["id"], r["code"], r["lvl"], r["has_page"], r["sphere"]) for r in rows("e4_dir")))
for r in rows("e5_prof"):
    db.execute("INSERT INTO prof VALUES(?,?)", (r["id"], r["has_page"]))
    db.executemany("INSERT INTO profdir VALUES(?,?)", ((r["id"], c) for c in set(arr(r["dirs"]))))
db.executemany("INSERT INTO country VALUES(?,?,?,?,?)", ((r["cc"], r["has_page"], r["ed_en_chars"], r["ed_ru_chars"], r["has_prep"]) for r in rows("e6_misc")))
db.executemany("INSERT INTO sphere VALUES(?,?,?,?,?)", ((r["id"], r["slug"], r["n_prog"], r["n_inst"], r["n_dir"]) for r in rows("e7_sphere")))
db.executemany("INSERT INTO ai VALUES(?,?,?,?,?,?,?)", ((r["kind"], r["source_ext_id"], r["section"], r["lang"], r["country"], r["state"], r["chars"]) for r in rows("e9_ai")))
db.executescript("""
CREATE INDEX p_cc ON p(cc, dir); CREATE INDEX p_inst ON p(inst); CREATE INDEX pl ON plang(id); CREATE INDEX py ON pyear(id);
CREATE INDEX i_key ON inst(ikey); CREATE INDEX c_cc ON city(cc, city);
""")
db.commit()
for t in "p plang pyear inst city dirs prof profdir country sphere ai fx".split():
    print(t, db.execute(f"SELECT count(*) FROM {t}").fetchone()[0])
```

### 8.4 Агрегаты (SQLite)

Временные таблицы (`analysis.py`):

```sql
-- programmes in the search index: listed, of a listed institution (crates/portal-sync/src/index.rs:175-195)
CREATE TEMP TABLE pv AS SELECT p.* FROM p JOIN inst i ON i.ikey = p.inst AND i.listed = 1;
CREATE INDEX temp.pv_id ON pv(id); CREATE INDEX temp.pv_cc ON pv(cc, city); CREATE INDEX temp.pv_inst ON pv(inst); CREATE INDEX temp.pv_dir ON pv(dir);
-- programmes of a direction that has a page (CIP family with a slug)
CREATE TEMP TABLE pd AS SELECT pv.* FROM pv JOIN dirs d ON d.code = pv.dir AND d.has_page = 1;
CREATE INDEX temp.pd_id ON pd(id); CREATE INDEX temp.pd_dir ON pd(dir); CREATE INDEX temp.pd_cc ON pd(cc, dir);
-- listed cities
CREATE TEMP TABLE lc AS SELECT * FROM city WHERE listed = 1;
CREATE INDEX temp.lc_cc ON lc(cc, city);
-- per-country totals (parent T01)
CREATE TEMP TABLE cn AS SELECT cc, count(*) n, count(DISTINCT inst) ni FROM pv GROUP BY cc;
-- per-city totals (parent T02)
CREATE TEMP TABLE ctn AS SELECT cc, city, count(*) n, count(DISTINCT inst) ni FROM pv GROUP BY cc, city;
-- T20 groups (parent of T21, T43)
CREATE TEMP TABLE t20 AS SELECT cc, dir, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np FROM pd GROUP BY cc, dir;
CREATE TEMP TABLE dn AS SELECT dir, count(DISTINCT cc) ncc FROM pd GROUP BY dir;
-- per (country, level) and (country, language) totals (parents T22, T23)
CREATE TEMP TABLE clvl AS SELECT cc, lvl, count(*) n FROM pv GROUP BY cc, lvl;
CREATE TEMP TABLE clang AS SELECT cc, lang, count(*) n FROM pv JOIN plang USING (id) GROUP BY cc, lang;
-- AI and editorial texts of at least 300 characters a visitor meets
CREATE TEMP VIEW txt AS SELECT kind, ext FROM ai WHERE chars >= 300 GROUP BY kind, ext;
```

Агрегаты — тексты запросов в порядке вывода. Пороги сценариев подставлены числами (мягкий 2/2, базовый 2/3, жёсткий 3/5):

```sql
-- S0 dictionary sizes
SELECT
 (SELECT count(*) FROM country) AS countries, (SELECT count(DISTINCT cc) FROM pv) AS countries_with_programs,
 (SELECT count(*) FROM city) AS city_docs, (SELECT count(*) FROM lc) AS cities_listed,
 (SELECT count(*) FROM (SELECT DISTINCT cc, city FROM pv WHERE city IS NOT NULL)) AS cities_with_programs,
 (SELECT count(*) FROM dirs WHERE lvl = 2) AS cip_series, (SELECT count(*) FROM dirs WHERE lvl = 4) AS cip_families,
 (SELECT count(*) FROM dirs WHERE lvl = 6) AS cip_codes, (SELECT count(*) FROM dirs WHERE has_page = 1) AS direction_pages,
 (SELECT count(*) FROM sphere) AS spheres, (SELECT count(*) FROM prof) AS professions,
 (SELECT count(*) FROM prof WHERE has_page = 1) AS profession_pages,
 (SELECT count(*) FROM pv) AS programs_in_index, (SELECT count(*) FROM pv WHERE is_var = 0) AS programs_main,
 (SELECT count(DISTINCT lvl) FROM pv) AS levels, (SELECT count(DISTINCT lang) FROM plang JOIN pv USING (id)) AS languages_used,
 (SELECT count(DISTINCT form) FROM pv) AS forms;

-- S1 programme fields (listed, institution listed)
SELECT count(*) AS programs, sum(priced) AS with_price,
 sum(fdl) AS with_future_deadline, sum(own_lang) AS with_own_language, sum(form IS NOT NULL) AS with_form,
 sum(dir IS NULL) AS without_direction, sum(eu) AS with_eu_price, sum(free) AS free_or_budget_places,
 sum(id IN (SELECT id FROM pyear)) AS with_any_dated_year
FROM pv;

-- T01 countries
WITH c AS (SELECT cc, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np FROM pv GROUP BY cc)
SELECT count(*) AS possible, sum(c.n IS NULL) AS k4_no_programs, sum(c.n IS NOT NULL) AS with_programs,
 sum(c.nd > 0) AS with_deadline, sum(c.np > 0) AS with_price,
 sum(c.n IS NOT NULL AND (co.ed_en >= 300 OR co.ed_ru >= 300 OR co.cc IN (SELECT ext FROM txt WHERE kind = 'country'))) AS with_text,
 sum(co.has_prep) AS with_ru_cases
FROM country co LEFT JOIN c ON c.cc = co.cc;

-- T02 cities
WITH c AS (SELECT cc, city, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np FROM pv GROUP BY cc, city),
 k AS (SELECT city.*, COALESCE(n_univ, 0) + COALESCE(n_coll, 0) AS ninst, c.n, c.nd, c.np, cn.n AS cn_n, cn.ni AS cn_ni, c.ni
       FROM city LEFT JOIN c ON c.cc = city.cc AND c.city = city.city LEFT JOIN cn ON cn.cc = city.cc)
SELECT count(*) AS possible,
 sum(listed = 0) AS k5_no_page, sum(listed = 1 AND ninst = 0) AS k5_no_institution,
 sum(listed = 1 AND ninst = 1) AS k3_single_institution,
 sum(listed = 1 AND ninst >= 2 AND n = cn_n AND ni = cn_ni) AS k3_same_as_country,
 sum(listed = 1 AND ninst >= 2 AND n IS NULL) AS k4_no_programs,
 sum(listed = 1 AND ninst >= 2 AND n IS NOT NULL AND NOT (n = cn_n AND ni = cn_ni)) AS k2_candidates,
 sum(listed = 1 AND ninst >= 2 AND n IS NOT NULL AND NOT (n = cn_n AND ni = cn_ni) AND nd > 0) AS k2_with_deadline,
 sum(listed = 1 AND ninst >= 2 AND n IS NOT NULL AND NOT (n = cn_n AND ni = cn_ni) AND np > 0) AS k2_with_price,
 sum(listed = 1 AND ninst = 1 AND n IS NOT NULL) AS single_inst_with_programs
FROM k;

-- T03/T04 institutions
WITH ip AS (SELECT inst, count(*) n, sum(fdl) nd, sum(dir IN (SELECT code FROM dirs WHERE has_page = 1)) ndir FROM pv GROUP BY inst),
 k AS (SELECT i.*, COALESCE(ip.n, 0) AS n, COALESCE(ip.nd, 0) AS nd, COALESCE(ip.ndir, 0) AS ndir,
   (has_name = 1 AND cc IS NOT NULL AND city IS NOT NULL AND category IN ('university', 'college') AND has_site = 1) AS ident,
   (has_contact + has_type + (COALESCE(ip.ndir, 0) > 0) + has_price + (COALESCE(ip.nd, 0) > 0) + has_coords) AS d1
   FROM inst i LEFT JOIN ip ON ip.inst = i.ikey)
SELECT category, count(*) AS possible, sum(merged) AS k5_merged_301, sum(listed = 0 AND merged = 0) AS k5_no_page,
 sum(listed = 1) AS listed, sum(listed = 1 AND n > 0) AS listed_with_programs, sum(listed = 1 AND ident = 1) AS with_identity,
 sum(listed = 1 AND ident = 1 AND d1 >= 4) AS k1_identity_d1_ge4,
 sum(listed = 1 AND ident = 1 AND d1 = 3 AND nd = 0) AS k2_only_deadline_missing,
 sum(listed = 1 AND NOT (ident = 1 AND d1 >= 4) AND NOT (ident = 1 AND d1 = 3 AND nd = 0)) AS k4,
 sum(listed = 1 AND has_site = 0) AS no_site, sum(listed = 1 AND city IS NULL) AS no_city,
 sum(listed = 1 AND has_contact = 1) AS d1_contact, sum(listed = 1 AND has_type = 1) AS d1_type,
 sum(listed = 1 AND ndir > 0) AS d1_directions, sum(listed = 1 AND has_price = 1) AS d1_price,
 sum(listed = 1 AND nd > 0) AS d1_deadline, sum(listed = 1 AND has_coords = 1) AS d1_coords
FROM k GROUP BY category;

-- T06 programmes
SELECT count(*) AS listed_programs, sum(is_var) AS k3_variants,
 sum(is_var = 0) AS main_programs,
 sum(is_var = 0 AND CAST(id AS TEXT) IN (SELECT ext FROM txt WHERE kind = 'program')) AS with_description,
 sum(is_var = 0 AND priced = 1) AS with_price,
 sum(is_var = 0 AND priced = 1 AND CAST(id AS TEXT) IN (SELECT ext FROM txt WHERE kind = 'program')) AS with_description_and_price,
 sum(is_var = 0 AND CAST(id AS TEXT) NOT IN (SELECT ext FROM txt WHERE kind = 'program')) AS k3_no_description,
 (SELECT count(*) FROM p) - count(*) AS listed_but_institution_not_listed
FROM pv;

-- T07 directions
WITH g AS (SELECT d.code, count(pd.id) n, count(DISTINCT pd.inst) ni, 0 AS dup FROM dirs d LEFT JOIN pd ON pd.dir = d.code
            WHERE d.lvl = 4 AND d.has_page = 1 GROUP BY d.code)
SELECT (SELECT count(*) FROM dirs WHERE lvl = 4) AS possible, count(*) AS with_page,
 sum(dup = 0 AND n >= 2 AND ni >= 2) AS pass_soft,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pass_base,
  sum(dup = 0 AND n >= 5 AND ni >= 3) AS pass_hard
FROM g;

-- T08 spheres (projection counts)
SELECT count(*) AS spheres, min(n_prog) AS min_programs, min(n_inst) AS min_institutions FROM sphere;

-- T09 professions
WITH pp AS (SELECT pr.id, count(DISTINCT pd.id) n, count(DISTINCT pd.inst) ni FROM prof pr
   LEFT JOIN profdir x ON x.prof = pr.id LEFT JOIN pd ON pd.dir = x.code GROUP BY pr.id)
SELECT count(*) AS possible, sum(pr.has_page = 0) AS k5_no_page,
 sum(pr.has_page = 1 AND (SELECT count(*) FROM profdir WHERE prof = pr.id) > 0) AS with_linked_directions,
 sum(pr.has_page = 1 AND pp.n > 0) AS with_linked_programs, sum(pr.has_page = 1 AND pp.n = 0) AS k4_no_programs,
 (SELECT count(*) FROM txt WHERE kind = 'profession') AS with_own_text
FROM prof pr JOIN pp ON pp.id = pr.id;

-- T20 direction x country
WITH g AS (SELECT t20.*, (dn.ncc = 1 OR t20.n = cn.n) AS dup FROM t20 JOIN dn USING (dir) JOIN cn USING (cc))
SELECT (SELECT count(*) FROM dirs WHERE has_page = 1) * (SELECT count(*) FROM country) AS possible, count(*) AS exist, sum(dup) AS k3_dup,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pass_soft,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pass_base,
  sum(dup = 0 AND n >= 5 AND ni >= 3) AS pass_hard,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd > 0) AS base_with_deadline,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND np > 0) AS base_with_price,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd = 0 AND np = 0) AS base_neither,
  sum(dup = 0 AND n >= 1 AND ni >= 2) AS pprog_1,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pprog_2,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pprog_3,
  sum(dup = 0 AND n >= 5 AND ni >= 2) AS pprog_5,
  sum(dup = 0 AND n >= 10 AND ni >= 2) AS pprog_10
FROM g;

-- T21 direction x city
WITH g AS (SELECT x.*, (x.n = t20.n OR x.n = ctn.n) AS dup FROM (SELECT cc, city, dir, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np FROM pd WHERE (cc, city) IN (SELECT cc, city FROM lc) GROUP BY cc, city, dir) x JOIN t20 USING (cc, dir) JOIN ctn USING (cc, city))
SELECT (SELECT count(*) FROM dirs WHERE has_page = 1) * (SELECT count(*) FROM lc) AS possible, count(*) AS exist, sum(dup) AS k3_dup,
  sum(dup = 0 AND ni >= 2) AS pass_soft,
  sum(dup = 0 AND ni >= 2) AS pass_base,
  sum(dup = 0 AND ni >= 3) AS pass_hard,
  sum(dup = 0 AND ni >= 2 AND nd > 0) AS base_with_deadline,
  sum(dup = 0 AND ni >= 2 AND np > 0) AS base_with_price,
  sum(dup = 0 AND ni >= 2 AND nd = 0 AND np = 0) AS base_neither,
  sum(dup = 0 AND n >= 1 AND ni >= 2) AS pprog_1,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pprog_2,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pprog_3,
  sum(dup = 0 AND n >= 5 AND ni >= 2) AS pprog_5,
  sum(dup = 0 AND n >= 10 AND ni >= 2) AS pprog_10
FROM g;

-- T22 level x country
WITH g AS (SELECT x.*, (x.n = cn.n) AS dup FROM (SELECT cc, lvl, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np FROM pv GROUP BY cc, lvl) x JOIN cn USING (cc))
SELECT 7 * (SELECT count(*) FROM country) AS possible, count(*) AS exist, sum(dup) AS k3_dup,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pass_soft,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pass_base,
  sum(dup = 0 AND n >= 5 AND ni >= 3) AS pass_hard,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd > 0) AS base_with_deadline,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND np > 0) AS base_with_price,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd = 0 AND np = 0) AS base_neither,
  sum(dup = 0 AND n >= 1 AND ni >= 2) AS pprog_1,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pprog_2,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pprog_3,
  sum(dup = 0 AND n >= 5 AND ni >= 2) AS pprog_5,
  sum(dup = 0 AND n >= 10 AND ni >= 2) AS pprog_10
FROM g;

-- T23 language x country
WITH g AS (SELECT x.*, (x.n = cn.n) AS dup FROM (SELECT cc, lang, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np FROM pv JOIN plang USING (id) GROUP BY cc, lang) x JOIN cn USING (cc))
SELECT 36 * (SELECT count(*) FROM country) AS possible, count(*) AS exist, sum(dup) AS k3_dup,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pass_soft,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pass_base,
  sum(dup = 0 AND n >= 5 AND ni >= 3) AS pass_hard,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd > 0) AS base_with_deadline,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND np > 0) AS base_with_price,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd = 0 AND np = 0) AS base_neither,
  sum(dup = 0 AND n >= 1 AND ni >= 2) AS pprog_1,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pprog_2,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pprog_3,
  sum(dup = 0 AND n >= 5 AND ni >= 2) AS pprog_5,
  sum(dup = 0 AND n >= 10 AND ni >= 2) AS pprog_10
FROM g;

-- T24 form x city
WITH g AS (SELECT x.*, (x.n = ctn.n) AS dup FROM (SELECT cc, city, form, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np FROM pv WHERE form IS NOT NULL AND (cc, city) IN (SELECT cc, city FROM lc) GROUP BY cc, city, form) x JOIN ctn USING (cc, city))
SELECT 4 * (SELECT count(*) FROM lc) AS possible, count(*) AS exist, sum(dup) AS k3_dup,
  sum(dup = 0 AND ni >= 2) AS pass_soft,
  sum(dup = 0 AND ni >= 2) AS pass_base,
  sum(dup = 0 AND ni >= 3) AS pass_hard,
  sum(dup = 0 AND ni >= 2 AND nd > 0) AS base_with_deadline,
  sum(dup = 0 AND ni >= 2 AND np > 0) AS base_with_price,
  sum(dup = 0 AND ni >= 2 AND nd = 0 AND np = 0) AS base_neither,
  sum(dup = 0 AND n >= 1 AND ni >= 2) AS pprog_1,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pprog_2,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pprog_3,
  sum(dup = 0 AND n >= 5 AND ni >= 2) AS pprog_5,
  sum(dup = 0 AND n >= 10 AND ni >= 2) AS pprog_10
FROM g;

-- T25 budget band x country
WITH g AS (SELECT x.*, (x.n = x.n_prev OR x.n = cn.n) AS dup FROM (SELECT cc, 1000 AS band, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np, (SELECT count(*) FROM pv q WHERE q.cc = pv.cc AND q.priced = 1 AND 0) AS n_prev FROM pv WHERE priced = 1 AND usd <= 1000 GROUP BY cc UNION ALL SELECT cc, 2000 AS band, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np, (SELECT count(*) FROM pv q WHERE q.cc = pv.cc AND q.priced = 1 AND q.usd <= 1000) AS n_prev FROM pv WHERE priced = 1 AND usd <= 2000 GROUP BY cc UNION ALL SELECT cc, 5000 AS band, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np, (SELECT count(*) FROM pv q WHERE q.cc = pv.cc AND q.priced = 1 AND q.usd <= 2000) AS n_prev FROM pv WHERE priced = 1 AND usd <= 5000 GROUP BY cc UNION ALL SELECT cc, 10000 AS band, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np, (SELECT count(*) FROM pv q WHERE q.cc = pv.cc AND q.priced = 1 AND q.usd <= 5000) AS n_prev FROM pv WHERE priced = 1 AND usd <= 10000 GROUP BY cc UNION ALL SELECT cc, 20000 AS band, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np, (SELECT count(*) FROM pv q WHERE q.cc = pv.cc AND q.priced = 1 AND q.usd <= 10000) AS n_prev FROM pv WHERE priced = 1 AND usd <= 20000 GROUP BY cc) x JOIN cn USING (cc))
SELECT 5 * (SELECT count(*) FROM country) AS possible, count(*) AS exist, sum(dup) AS k3_dup,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pass_soft,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pass_base,
  sum(dup = 0 AND n >= 5 AND ni >= 3) AS pass_hard,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd > 0) AS base_with_deadline,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND np > 0) AS base_with_price,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd = 0 AND np = 0) AS base_neither,
  sum(dup = 0 AND n >= 1 AND ni >= 2) AS pprog_1,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pprog_2,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pprog_3,
  sum(dup = 0 AND n >= 5 AND ni >= 2) AS pprog_5,
  sum(dup = 0 AND n >= 10 AND ni >= 2) AS pprog_10
FROM g;

-- T26 profession x country
WITH g AS (SELECT x.*, (x.ndir = 1 OR x.n = cn.n) AS dup FROM (SELECT pr.id, pd.cc, count(DISTINCT pd.id) n, count(DISTINCT pd.inst) ni, count(DISTINCT pd.dir) ndir, sum(pd.fdl) nd, sum(pd.priced) np FROM prof pr JOIN profdir x ON x.prof = pr.id JOIN pd ON pd.dir = x.code WHERE pr.has_page = 1 GROUP BY pr.id, pd.cc) x JOIN cn USING (cc))
SELECT (SELECT count(*) FROM prof WHERE has_page = 1) * (SELECT count(*) FROM country) AS possible, count(*) AS exist, sum(dup) AS k3_dup,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pass_soft,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pass_base,
  sum(dup = 0 AND n >= 5 AND ni >= 3) AS pass_hard,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd > 0) AS base_with_deadline,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND np > 0) AS base_with_price,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd = 0 AND np = 0) AS base_neither,
  sum(dup = 0 AND n >= 1 AND ni >= 2) AS pprog_1,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pprog_2,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pprog_3,
  sum(dup = 0 AND n >= 5 AND ni >= 2) AS pprog_5,
  sum(dup = 0 AND n >= 10 AND ni >= 2) AS pprog_10
FROM g;

-- T43 S4 country+direction+level
WITH g AS (SELECT x.*, (x.n = t20.n OR x.n = clvl.n) AS dup FROM (SELECT cc, dir, lvl, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np FROM pd GROUP BY cc, dir, lvl) x JOIN t20 USING (cc, dir) JOIN clvl USING (cc, lvl))
SELECT (SELECT count(*) FROM country) * (SELECT count(*) FROM dirs WHERE has_page = 1) * 7 AS possible, count(*) AS exist, sum(dup) AS k3_dup,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pass_soft,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pass_base,
  sum(dup = 0 AND n >= 5 AND ni >= 3) AS pass_hard,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd > 0) AS base_with_deadline,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND np > 0) AS base_with_price,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd = 0 AND np = 0) AS base_neither,
  sum(dup = 0 AND n >= 1 AND ni >= 2) AS pprog_1,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pprog_2,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pprog_3,
  sum(dup = 0 AND n >= 5 AND ni >= 2) AS pprog_5,
  sum(dup = 0 AND n >= 10 AND ni >= 2) AS pprog_10
FROM g;

-- T43 S5 country+direction+language
WITH g AS (SELECT x.*, (x.n = t20.n OR x.n = clang.n) AS dup FROM (SELECT cc, dir, lang, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np FROM pd JOIN plang USING (id) GROUP BY cc, dir, lang) x JOIN t20 USING (cc, dir) JOIN clang USING (cc, lang))
SELECT (SELECT count(*) FROM country) * (SELECT count(*) FROM dirs WHERE has_page = 1) * 36 AS possible, count(*) AS exist, sum(dup) AS k3_dup,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pass_soft,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pass_base,
  sum(dup = 0 AND n >= 5 AND ni >= 3) AS pass_hard,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd > 0) AS base_with_deadline,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND np > 0) AS base_with_price,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd = 0 AND np = 0) AS base_neither,
  sum(dup = 0 AND n >= 1 AND ni >= 2) AS pprog_1,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pprog_2,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pprog_3,
  sum(dup = 0 AND n >= 5 AND ni >= 2) AS pprog_5,
  sum(dup = 0 AND n >= 10 AND ni >= 2) AS pprog_10
FROM g;

-- T43 S6 country+direction+level+language
WITH g AS (SELECT x.*, (x.n = s4.n OR x.n = s5.n) AS dup FROM (SELECT cc, dir, lvl, lang, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np FROM pd JOIN plang USING (id) GROUP BY cc, dir, lvl, lang) x JOIN (SELECT cc, dir, lvl, count(*) n FROM pd GROUP BY cc, dir, lvl) s4 USING (cc, dir, lvl) JOIN (SELECT cc, dir, lang, count(*) n FROM pd JOIN plang USING (id) GROUP BY cc, dir, lang) s5 USING (cc, dir, lang))
SELECT (SELECT count(*) FROM country) * (SELECT count(*) FROM dirs WHERE has_page = 1) * 7 * 36 AS possible, count(*) AS exist, sum(dup) AS k3_dup,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pass_soft,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pass_base,
  sum(dup = 0 AND n >= 5 AND ni >= 3) AS pass_hard,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd > 0) AS base_with_deadline,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND np > 0) AS base_with_price,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd = 0 AND np = 0) AS base_neither,
  sum(dup = 0 AND n >= 1 AND ni >= 2) AS pprog_1,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pprog_2,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pprog_3,
  sum(dup = 0 AND n >= 5 AND ni >= 2) AS pprog_5,
  sum(dup = 0 AND n >= 10 AND ni >= 2) AS pprog_10
FROM g;

-- T43 S7 country+direction+level+free
WITH g AS (SELECT x.*, (x.n = s4.n) AS dup FROM (SELECT cc, dir, lvl, count(*) n, count(DISTINCT inst) ni, sum(fdl) nd, sum(priced) np FROM pd WHERE free = 1 GROUP BY cc, dir, lvl) x JOIN (SELECT cc, dir, lvl, count(*) n FROM pd GROUP BY cc, dir, lvl) s4 USING (cc, dir, lvl))
SELECT (SELECT count(*) FROM country) * (SELECT count(*) FROM dirs WHERE has_page = 1) * 7 AS possible, count(*) AS exist, sum(dup) AS k3_dup,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pass_soft,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pass_base,
  sum(dup = 0 AND n >= 5 AND ni >= 3) AS pass_hard,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd > 0) AS base_with_deadline,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND np > 0) AS base_with_price,
  sum(dup = 0 AND n >= 3 AND ni >= 2 AND nd = 0 AND np = 0) AS base_neither,
  sum(dup = 0 AND n >= 1 AND ni >= 2) AS pprog_1,
  sum(dup = 0 AND n >= 2 AND ni >= 2) AS pprog_2,
  sum(dup = 0 AND n >= 3 AND ni >= 2) AS pprog_3,
  sum(dup = 0 AND n >= 5 AND ni >= 2) AS pprog_5,
  sum(dup = 0 AND n >= 10 AND ni >= 2) AS pprog_10
FROM g;

-- T43 facet values to write (base, pages over thresholds, not duplicates)
WITH s4 AS (
  SELECT x.cc, x.dir, x.lvl FROM (SELECT cc, dir, lvl, count(*) n, count(DISTINCT inst) ni FROM pd GROUP BY cc, dir, lvl) x JOIN t20 USING (cc, dir)
  JOIN clvl USING (cc, lvl) WHERE x.n >= 3 AND x.ni >= 2 AND x.n <> t20.n AND x.n <> clvl.n),
 s5 AS (
  SELECT x.cc, x.dir, x.lang FROM (SELECT cc, dir, lang, count(*) n, count(DISTINCT inst) ni FROM pd JOIN plang USING (id) GROUP BY cc, dir, lang) x JOIN t20 USING (cc, dir)
  JOIN clang USING (cc, lang) WHERE x.n >= 3 AND x.ni >= 2 AND x.n <> t20.n AND x.n <> clang.n)
SELECT (SELECT count(DISTINCT cc) FROM (SELECT cc FROM s4 UNION SELECT cc FROM s5)) AS dest_countries,
 (SELECT count(DISTINCT dir) FROM (SELECT dir FROM s4 UNION SELECT dir FROM s5)) AS directions,
 (SELECT count(DISTINCT lvl) FROM s4) AS levels, (SELECT count(DISTINCT lang) FROM s5) AS languages;

-- T43 year facet: (combination, intake year >= 2027) with dated programmes, base thresholds
WITH yr AS (SELECT id, year FROM pyear WHERE year >= 2027)
SELECT
 (SELECT count(*) FROM (SELECT cc, dir, year FROM pd JOIN yr USING (id) GROUP BY cc, dir, year HAVING count(*) >= 3 AND count(DISTINCT inst) >= 2)) AS t20_year,
 (SELECT count(*) FROM (SELECT cc, lvl, year FROM pv JOIN yr USING (id) GROUP BY cc, lvl, year HAVING count(*) >= 3 AND count(DISTINCT inst) >= 2)) AS t22_year,
 (SELECT count(*) FROM (SELECT cc, lang, year FROM pv JOIN plang USING (id) JOIN yr USING (id) GROUP BY cc, lang, year HAVING count(*) >= 3 AND count(DISTINCT inst) >= 2)) AS t23_year,
 (SELECT count(*) FROM (SELECT cc, dir, lvl, year FROM pd JOIN yr USING (id) GROUP BY cc, dir, lvl, year HAVING count(*) >= 3 AND count(DISTINCT inst) >= 2)) AS s4_year,
 (SELECT count(*) FROM (SELECT cc, dir, lang, year FROM pd JOIN plang USING (id) JOIN yr USING (id) GROUP BY cc, dir, lang, year HAVING count(*) >= 3 AND count(DISTINCT inst) >= 2)) AS s5_year,
 (SELECT count(*) FROM (SELECT cc, dir, lvl, lang, year FROM pd JOIN plang USING (id) JOIN yr USING (id) GROUP BY cc, dir, lvl, lang, year HAVING count(*) >= 3 AND count(DISTINCT inst) >= 2)) AS s6_year,
 (SELECT count(*) FROM (SELECT cc, dir, lvl, year FROM pd JOIN yr USING (id) WHERE free = 1 GROUP BY cc, dir, lvl, year HAVING count(*) >= 3 AND count(DISTINCT inst) >= 2)) AS s7_year,
 (SELECT count(*) FROM (SELECT cc, city, dir, year FROM pd JOIN yr USING (id) WHERE (cc, city) IN (SELECT cc, city FROM lc) GROUP BY cc, city, dir, year HAVING count(DISTINCT inst) >= 2)) AS t21_year,
 (SELECT group_concat(year || ':' || n) FROM (SELECT year, count(DISTINCT cc) n FROM pv JOIN pyear USING (id) GROUP BY year ORDER BY year)) AS countries_by_year;

-- T25 shares and rates
SELECT (SELECT count(*) FROM pv WHERE priced = 1) AS priced, (SELECT count(*) FROM pv WHERE priced = 1 AND usd <= 1000) AS le_1000,
 (SELECT count(*) FROM pv WHERE priced = 1 AND usd <= 20000) AS le_20000, (SELECT max(per_usd) FROM fx WHERE currency = 'EUR') AS eur_per_usd;

-- T30 country -> country
WITH mk(cc) AS (VALUES ('AE'),('AM'),('AZ'),('GB'),('GE'),('KZ'),('RU'),('TR'),('UZ')),
 eu(cc) AS (VALUES ('AT'),('BE'),('BG'),('HR'),('CY'),('CZ'),('DK'),('EE'),('FI'),('FR'),('DE'),('GR'),('HU'),('IE'),('IT'),('LV'),('LT'),('LU'),('MT'),('NL'),('PL'),('PT'),('RO'),('SK'),('SI'),('ES'),('SE')),
 o AS (SELECT co.cc, co.cc IN (SELECT cc FROM mk) AS m, co.cc IN (SELECT cc FROM eu) AS e FROM country co),
 d AS (SELECT cc, sum(priced) np, sum(eu) neu FROM pv GROUP BY cc),
 dk AS (SELECT cc, np > 0 AS hp, neu > 0 AS he, count(*) k FROM d GROUP BY 1, 2, 3),
 pr AS (SELECT o.cc AS o, dk.k, (o.m = 1 AND dk.hp) + (o.e = 1 AND dk.he) AS blocks FROM o JOIN dk ON dk.cc <> o.cc)
SELECT (SELECT count(*) FROM country) * (SELECT count(*) FROM d) AS dest_x_origins, (SELECT count(*) FROM d) AS destinations,
 sum(k) AS created, sum(k * (blocks = 0)) AS b0, sum(k * (blocks = 1)) AS b1, sum(k * (blocks >= 2)) AS b2,
 count(DISTINCT CASE WHEN blocks >= 1 THEN o END) AS origins_with_data,
 (SELECT count(*) FROM o WHERE m = 1) AS market_origins, (SELECT count(*) FROM o WHERE e = 1) AS eu_origins_in_dictionary
FROM pr;

-- T34 country -> city
WITH mk(cc) AS (VALUES ('AE'),('AM'),('AZ'),('GB'),('GE'),('KZ'),('RU'),('TR'),('UZ')),
 eu(cc) AS (VALUES ('AT'),('BE'),('BG'),('HR'),('CY'),('CZ'),('DK'),('EE'),('FI'),('FR'),('DE'),('GR'),('HU'),('IE'),('IT'),('LV'),('LT'),('LU'),('MT'),('NL'),('PL'),('PT'),('RO'),('SK'),('SI'),('ES'),('SE')),
 o AS (SELECT co.cc, co.cc IN (SELECT cc FROM mk) AS m, co.cc IN (SELECT cc FROM eu) AS e FROM country co),
 d AS (SELECT cc, city, sum(priced) np, sum(eu) neu FROM pv WHERE (cc, city) IN (SELECT cc, city FROM lc) GROUP BY cc, city),
 dk AS (SELECT cc, np > 0 AS hp, neu > 0 AS he, count(*) k FROM d GROUP BY 1, 2, 3),
 pr AS (SELECT o.cc AS o, dk.k, (o.m = 1 AND dk.hp) + (o.e = 1 AND dk.he) AS blocks FROM o JOIN dk ON dk.cc <> o.cc)
SELECT (SELECT count(*) FROM country) * (SELECT count(*) FROM d) AS dest_x_origins, (SELECT count(*) FROM d) AS destinations,
 sum(k) AS created, sum(k * (blocks = 0)) AS b0, sum(k * (blocks = 1)) AS b1, sum(k * (blocks >= 2)) AS b2,
 count(DISTINCT CASE WHEN blocks >= 1 THEN o END) AS origins_with_data,
 (SELECT count(*) FROM o WHERE m = 1) AS market_origins, (SELECT count(*) FROM o WHERE e = 1) AS eu_origins_in_dictionary
FROM pr;

-- T35 country -> institution
WITH mk(cc) AS (VALUES ('AE'),('AM'),('AZ'),('GB'),('GE'),('KZ'),('RU'),('TR'),('UZ')),
 eu(cc) AS (VALUES ('AT'),('BE'),('BG'),('HR'),('CY'),('CZ'),('DK'),('EE'),('FI'),('FR'),('DE'),('GR'),('HU'),('IE'),('IT'),('LV'),('LT'),('LU'),('MT'),('NL'),('PL'),('PT'),('RO'),('SK'),('SI'),('ES'),('SE')),
 o AS (SELECT co.cc, co.cc IN (SELECT cc FROM mk) AS m, co.cc IN (SELECT cc FROM eu) AS e FROM country co),
 d AS (SELECT cc, inst, sum(priced) np, sum(eu) neu FROM pv GROUP BY cc, inst),
 dk AS (SELECT cc, np > 0 AS hp, neu > 0 AS he, count(*) k FROM d GROUP BY 1, 2, 3),
 pr AS (SELECT o.cc AS o, dk.k, (o.m = 1 AND dk.hp) + (o.e = 1 AND dk.he) AS blocks FROM o JOIN dk ON dk.cc <> o.cc)
SELECT (SELECT count(*) FROM country) * (SELECT count(*) FROM d) AS dest_x_origins, (SELECT count(*) FROM d) AS destinations,
 sum(k) AS created, sum(k * (blocks = 0)) AS b0, sum(k * (blocks = 1)) AS b1, sum(k * (blocks >= 2)) AS b2,
 count(DISTINCT CASE WHEN blocks >= 1 THEN o END) AS origins_with_data,
 (SELECT count(*) FROM o WHERE m = 1) AS market_origins, (SELECT count(*) FROM o WHERE e = 1) AS eu_origins_in_dictionary
FROM pr;

-- T36 country -> programme
WITH mk(cc) AS (VALUES ('AE'),('AM'),('AZ'),('GB'),('GE'),('KZ'),('RU'),('TR'),('UZ')),
 eu(cc) AS (VALUES ('AT'),('BE'),('BG'),('HR'),('CY'),('CZ'),('DK'),('EE'),('FI'),('FR'),('DE'),('GR'),('HU'),('IE'),('IT'),('LV'),('LT'),('LU'),('MT'),('NL'),('PL'),('PT'),('RO'),('SK'),('SI'),('ES'),('SE')),
 o AS (SELECT co.cc, co.cc IN (SELECT cc FROM mk) AS m, co.cc IN (SELECT cc FROM eu) AS e FROM country co),
 d AS (SELECT cc, id, priced np, eu neu FROM pv),
 dk AS (SELECT cc, np > 0 AS hp, neu > 0 AS he, count(*) k FROM d GROUP BY 1, 2, 3),
 pr AS (SELECT o.cc AS o, dk.k, (o.m = 1 AND dk.hp) + (o.e = 1 AND dk.he) AS blocks FROM o JOIN dk ON dk.cc <> o.cc)
SELECT (SELECT count(*) FROM country) * (SELECT count(*) FROM d) AS dest_x_origins, (SELECT count(*) FROM d) AS destinations,
 sum(k) AS created, sum(k * (blocks = 0)) AS b0, sum(k * (blocks = 1)) AS b1, sum(k * (blocks >= 2)) AS b2,
 count(DISTINCT CASE WHEN blocks >= 1 THEN o END) AS origins_with_data,
 (SELECT count(*) FROM o WHERE m = 1) AS market_origins, (SELECT count(*) FROM o WHERE e = 1) AS eu_origins_in_dictionary
FROM pr;

-- T30 origins ranked by destinations with data (top 10)
WITH mk(cc) AS (VALUES ('AE'),('AM'),('AZ'),('GB'),('GE'),('KZ'),('RU'),('TR'),('UZ')),
 eu(cc) AS (VALUES ('AT'),('BE'),('BG'),('HR'),('CY'),('CZ'),('DK'),('EE'),('FI'),('FR'),('DE'),('GR'),('HU'),('IE'),('IT'),('LV'),('LT'),('LU'),('MT'),('NL'),('PL'),('PT'),('RO'),('SK'),('SI'),('ES'),('SE')),
 o AS (SELECT co.cc, co.cc IN (SELECT cc FROM mk) AS m, co.cc IN (SELECT cc FROM eu) AS e FROM country co),
 d AS (SELECT cc, sum(priced) np, sum(eu) neu FROM pv GROUP BY cc)
SELECT o.cc, sum((o.m = 1 AND d.np > 0) + (o.e = 1 AND d.neu > 0)) AS blocks_total, sum((o.m = 1 AND d.np > 0) OR (o.e = 1 AND d.neu > 0)) AS dests_with_data
FROM o JOIN d ON d.cc <> o.cc GROUP BY o.cc HAVING dests_with_data > 0 ORDER BY dests_with_data DESC, o.cc LIMIT 10;

-- eu-price destinations
SELECT cc, count(*) FROM pv WHERE eu = 1 GROUP BY cc;

-- T40 pairs
SELECT (SELECT count(*) FROM inst WHERE listed = 1) AS n_inst, (SELECT count(*) FROM pv WHERE is_var = 0) AS n_prog;

-- T50-T53 coordinates
SELECT sum(listed = 1) AS listed_institutions, sum(listed = 1 AND has_coords = 1) AS with_coords FROM inst;

-- Consistency: city page count vs index count
WITH c AS (SELECT cc, city, count(*) n FROM pv GROUP BY cc, city)
SELECT count(*) AS cities_listed, sum(COALESCE(lc.n_prog, 0) = COALESCE(c.n, 0)) AS equal,
 sum(COALESCE(lc.n_prog, 0) > COALESCE(c.n, 0)) AS page_more, sum(COALESCE(lc.n_prog, 0) < COALESCE(c.n, 0)) AS page_less,
 sum(COALESCE(lc.n_prog, 0)) AS page_total, sum(COALESCE(c.n, 0)) AS index_total
FROM lc LEFT JOIN c ON c.cc = lc.cc AND c.city = lc.city;

-- AI texts
SELECT kind, section, count(*), sum(chars >= 300) FROM ai WHERE lang = 'en' GROUP BY kind, section;
```

```sql
-- S3 countries with programmes in the index, and those with a future programme deadline (block B05 today)
SELECT group_concat(cc) AS with_programs FROM (SELECT p.cc FROM p JOIN inst i ON i.ikey = p.inst AND i.listed = 1 GROUP BY p.cc);
SELECT group_concat(cc) AS with_future_deadline FROM (SELECT p.cc FROM p JOIN inst i ON i.ikey = p.inst AND i.listed = 1 GROUP BY p.cc HAVING sum(p.fdl) > 0);

-- S4 country page count (doc.body.counts.programs, E10) vs programmes in the index (listed, institution listed)
CREATE TEMP TABLE cp_raw(cc TEXT, n TEXT);
.mode tabs
.import x/country_page.tsv cp_raw
CREATE TEMP TABLE cp AS SELECT cc, CAST(n AS INT) n FROM cp_raw WHERE cc GLOB '[A-Z][A-Z]' AND n GLOB '[0-9]*';
.mode list
.separator ' | '
.headers on
WITH pvc AS (SELECT p.cc, count(*) n FROM p JOIN inst i ON i.ikey = p.inst AND i.listed = 1 GROUP BY p.cc)
SELECT count(*) AS countries, sum(cp.n = COALESCE(pvc.n, 0)) AS equal, sum(cp.n) AS page_total, sum(COALESCE(pvc.n, 0)) AS index_total
FROM cp LEFT JOIN pvc USING (cc);
WITH pvc AS (SELECT p.cc, count(*) n FROM p JOIN inst i ON i.ikey = p.inst AND i.listed = 1 GROUP BY p.cc)
SELECT cp.cc, cp.n AS page, COALESCE(pvc.n, 0) AS idx FROM cp LEFT JOIN pvc USING (cc) WHERE cp.n <> COALESCE(pvc.n, 0) ORDER BY cp.n DESC;
```

Строки темы: число листьев JSON в `themes/kuda/lang/{en,ru,tr,ar}.json`:

```bash
for f in en ru tr ar; do python3 -I -c "import json,sys
def c(x): return sum(map(c, x.values())) if isinstance(x, dict) else 1
print(sys.argv[1], c(json.load(open(sys.argv[1]))))" themes/kuda/lang/$f.json; done
```
