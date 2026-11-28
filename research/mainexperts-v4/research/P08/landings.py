"""Resolve ambiguous registry phrases through all source observations and enumerate public URLs."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote,urlsplit
import duckdb

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('workspace',type=Path)
p.add_argument('--queue',action='store_true')
a=p.parse_args()
w=a.workspace.resolve();d=w/'data'
con=duckdb.connect()
con.read_parquet(str(d/'observations_pending.parquet')).create_view('observations')
if not a.queue:
    relevant=r'(?i)(?:cricos\.education\.gov\.au|training\.gov\.au|teqsa\.gov\.au|educacion\.gob\.es/ruct|ciencia\.gob\.es/.{0,80}ruct|chea\.org|ope\.ed\.gov/dapip|aacsb\.edu|officeforstudents\.org\.uk/.{0,70}register|gov\.uk/check-a-university|francecompetences\.fr/.{0,30}(?:recherche|rncp)|enseignementsup-recherche\.gouv\.fr/.{0,40}bo|onisep\.fr/.{0,90}(?:rncp|visa|reconnaissance)|vuzopedia\.ru/(?:check-licens|articles/11920)|obrnadzor\.gov\.ru|postupi\.online/.{0,100}(?:akkredit|licenz|licens|proverit)|(?:caa|moe|mohesr)\.gov\.ae|khda\.gov\.ae|registries\.edu\.hk|hkcaavq\.edu\.hk|eqar\.eu|akkreditierungsrat\.de|fernstudium-staatlich-anerkannt|swissuniversities\.ch/.{0,60}akkredit|moe\.gov\.cn/.{0,80}20240619|uaeu\.ac\.ae/.{0,80}accredit|accreditation|accreditation|akkreditierung|license-verification|licence-check)'
    keys=con.execute("select distinct query_id from observations where regexp_matches(coalesce(target_url,''),?) order by query_id",[relevant]).fetchall()
    (d/'register-keys.txt').write_text(''.join(k+'\n' for (k,) in keys))
else:
    con.read_csv(str(w/'review_labels.csv'),header=True,all_varchar=True).create_view('review')
    found=con.execute("""select target_url,count(*) from observations join review using(query_id)
         where decision='accept' and target_url is not null and target_url<>'' group by 1 order by count(*) desc,target_url""").fetchall()
    valid=[]; skipped=[]
    for url,_ in found:
        reason=''
        try:
            link=urlsplit(url)
            host=(link.hostname or '').lower()
        except ValueError:
            reason='Адрес носит технический либо неполный формат'
        if not reason:
            if link.scheme not in ('https','http') or not re.fullmatch(r'[a-z0-9][a-z0-9.\-]*\.[a-z]{2,24}',host) or link.username or link.password:
                reason='Адрес не прошёл проверку публичного HTTP(S) имени'
            elif re.search(r'(?:token|session|credential|auth|email|phone|password|user_id|key)=',unquote(link.query),re.I):
                reason='Параметры адреса могут содержать данные пользователя'
        if reason:skipped.append({'url':url,'current_url':'','title':'','lines':0,'status':'reader_not_attempted','error':reason})
        else:valid.append(url)
    (d/'reader-queue.json').write_text(json.dumps(valid,ensure_ascii=False))
    (d/'reader-skipped.json').write_text(json.dumps(skipped,ensure_ascii=False))
    print('Distinct addresses for reading',len(valid),'excluded input addresses',len(skipped))
