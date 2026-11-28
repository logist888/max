"""Join P08 query adjudication, projects, precise route evidence and screenshot metadata."""
import argparse
import csv
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import duckdb
from PIL import Image

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('workspace',type=Path)
p.add_argument('release',type=Path)
a=p.parse_args()
W=a.workspace.resolve(); D=W/'data'; O=a.release.resolve(); T=O/'data'; T.mkdir(parents=True,exist_ok=True)
DATE='2026-11-28'
FAMILIES={
 'K029':('Q08.02b','Аккредитация и авторизация программы'),
 'K030':('Q08.01','Лицензия и статус организации'),
 'K031':('Q08.05','Запись в официальном реестре'),
 'K135':('Q08.11','Сверка кода CRICOS с курсом или провайдером'),
 'P08-K30':('Q08.04','Право присуждать квалификацию'),
 'P08-K31':('Q08.03','Охват статуса по площадке, сроку и форме'),
 'P08-K32':('Q08.08','Изменение или прекращение статуса'),
}

def read_csv(path):
 with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def write_csv(name,records,fields=None):
 with (T/(name+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
  if fields is None: fields=list(dict.fromkeys(k for row in records for k in row))
  writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(records)
def write_json(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def clean_host(h):
 h=(h or '').lower().removeprefix('www.').rstrip('.')
 return {'msk.postupi.online':'postupi.online','studyinhongkong.edu.hk':'studyinhongkong.edu.hk',
  'en.moe.gov.cn':'moe.gov.cn','internationalschools.edb.gov.hk':'edb.gov.hk','bigfuture.collegeboard.org':'collegeboard.org',
  'admission.universityofcalifornia.edu':'universityofcalifornia.edu','es.education.gouv.fr':'education.gouv.fr',
  'cicic.ca-851-education.canada':'cicic.ca','letudiant.fr-orientation.html':'letudiant.fr'}.get(h,h)
def pu(url):
 try: return urlsplit(url or '')
 except ValueError:return urlsplit('')
def exact_url(url):
 p=pu(url)
 if p.scheme not in ('http','https') or not p.hostname: return ''
 return urlunsplit(('https',(p.hostname or '').lower().removeprefix('www.'),p.path.rstrip('/') or '/',p.query,''))
def source_group(o):
 nominal=clean_host(o['nominal_domain']); actual=clean_host(o['landing_host']);
 if o['sha256'] in ambiguous_hashes:
  return actual or 'unresolved-sha-'+o['sha256'][:12]
 if nominal in ('bigfuture.xlsx','educatly.xlsx') or not nominal or '.' not in nominal: return actual or nominal or 'source-without-domain'
 return nominal

def tabular(con,sql):
 res=con.execute(sql); cols=[c[0] for c in res.description]
 while batch:=res.fetchmany(5000):
  yield from (dict(zip(cols,x)) for x in batch)

q_rows=read_csv(D/'queries_pending.csv')
adjudication={r['query_id']:r for r in read_csv(W/'review_labels.csv')}
route_sets=['europe','supplement','commercial']
raw_routes=[r for region in route_sets for r in load(W/(region+'.json'))]
assert len(raw_routes)==len({r['id'] for r in raw_routes})
routes_by_id={r['id']:r for r in raw_routes}
meta=load(D/'base.json')
assert len(q_rows)==meta['candidates']
judged=[]; keys={}; provenance={}; count_d=Counter()
for q in q_rows:
 override=adjudication.get(q['query_id'],{})
 assert override, (q['query_id'],q['resolution'])
 decision=override.get('decision',''); cluster=override.get('cluster') or q['cluster']
 note=override.get('note') or 'Правило отбора и независимая проверка'
 level=override.get('evidence') or 'D1'
 assert decision in ('accept','exclude','adjacent','residual','ambient'), (decision,q['query_id'])
 judged.append({**q,'decision':decision,'accepted_cluster':cluster,'evidence':level if decision=='accept' else '','review_note':note})
 if decision!='accept':continue
 assert cluster in FAMILIES,(cluster,q['query_id'])
 intent=override['intent']
 keys[q['query_id']]={
  'QUERY_ID':q['query_id'],'QUERY_RAW':q['query_raw'],'QUERY_NORMALIZED':q['query_normalized'],
  'LANGUAGE':q['language'] or 'und','SEARCH_MARKET':q['search_market'],'SEARCH_ENGINE':q['search_engine'],
  'VOLUME':q['volume'],'CPC':q['cpc'],'KD':q['kd'],'VOLUME_METRIC':q['volume_metric'],
  'CLUSTER_BASE_ID':cluster,'CLUSTER_ID':cluster+'-'+intent,'TASK_ID':FAMILIES[cluster][0],
  'INTENT_ID':intent,'EVIDENCE_LEVEL':level,'REASON':note,'SOURCE_REGION':'','DESTINATION':'','SOURCE_ID':'','OBSERVED_DATE':'',
 }
 count_d[level]+=1
assert set(adjudication)=={q['query_id'] for q in q_rows}
write_csv('adjudication',judged)
write_csv('queries',list(keys.values()))
con=duckdb.connect(); search_parquet=str((D/'observations_pending.parquet')).replace("'","''")
assert con.execute(f"select count(*) from read_parquet('{search_parquet}')").fetchone()[0]==meta['candidate_observations']
all_obs=tabular(con,f"select * from read_parquet('{search_parquet}') order by query_id,source_id,sheet,row_no")
shutil.copy2(D/'observations_pending.parquet',T/'candidate_observations.parquet')
obs=[]; projects=defaultdict(lambda:{'keys':set(),'sources':set(),'folders':set(),'landings':set(),'nominals':set(),'routes':[],'obs':0})
source_inventory=read_csv(D/'source_inventory.csv')
hash_domains=defaultdict(set)
for source in source_inventory:
 domain=clean_host(source['nominal_domain'])
 if source['sha256'] and domain:
  hash_domains[source['sha256']].add(domain)
ambiguous_hashes={h for h,domains in hash_domains.items() if len(domains)>1}
for s in source_inventory:
 group=clean_host(s['nominal_domain'])
 if group and '.' in group and group not in ('bigfuture.xlsx','educatly.xlsx'):
  projects[group]['nominals'].add(s['nominal_domain'])
landings=defaultdict(lambda:{'keys':set(),'clusters':set(),'regions':set(),'examples':[]})
exact=defaultdict(list); by_file=defaultdict(list); regions=defaultdict(lambda:{'keys':set(),'sites':set(),'obs':0}); markets=defaultdict(lambda:{'keys':set(),'sites':set(),'obs':0}); cluster_markets=defaultdict(set)
for source in all_obs:
 group=source_group(source); pr=projects[group]; pr['nominals'].add(source['nominal_domain'] or '')
 cluster=keys.get(source['query_id'])
 if not cluster:continue
 identity='O-'+hashlib.sha1(f"{source['source_id']}\t{source['sheet']}\t{source['row_no']}".encode()).hexdigest()[:22]
 o={**source,'observation_id':identity,'PROJECT_ID':group}
 obs.append(o); by_file[o['source_id']].append(o)
 cluster_id=cluster['CLUSTER_BASE_ID']
 if not cluster['SOURCE_ID']:
  cluster['SOURCE_ID']=o['source_id'];cluster['SOURCE_REGION']=o['source_region'];cluster['OBSERVED_DATE']=o['observed_date']
 url=exact_url(o['target_url'])
 if url:exact[url].append(o);pr['landings'].add(url)
 pr['obs']+=1;pr['keys'].add(o['query_id']);pr['sources'].add(o['source_id']);pr['folders'].add(o['source_region'])
 l=landings[(group,o['nominal_domain'],o['landing_host'],o['target_url'])];l['keys'].add(o['query_id']);l['clusters'].add(cluster_id);l['regions'].add(o['source_region']);l['examples'].append(o['query_id'])
 for out,i in [(regions,o['source_region']),(markets,(o['search_engine'] or '',o['search_market'] or '',cluster['LANGUAGE'] or ''))]:
  b=out[i];b['obs']+=1;b['keys'].add(o['query_id']);b['sites'].add(group)
 cluster_markets[(cluster_id,cluster['INTENT_ID'],o['search_market'] or '',cluster['LANGUAGE'] or '',o['search_engine'] or '',o['volume_metric'] or '')].add(o['query_id'])
assert len({x['observation_id'] for x in obs})==len(obs)
write_csv('queries',list(keys.values()))
write_csv('observations',obs)
reader={x['url']:x for x in load(D/'web_audit.json')}; reader_norm={exact_url(k):v for k,v in reader.items() if exact_url(k)}
write_csv('public_reader_audit',list(reader.values()))

paths=[]; steps=[]; links=[]; matched_projects=set(); report_routes=[]; titles={}
def label_payment(x):
 raw=x.get('payment_type',''); v=raw.lower()
 if v in ('institution_paid','b2b','institutional_paid','institutional_only','provider_paid','sponsored_listing','b2b_institutional'):return 'institutional_paid'
 if v in ('priced_listed','priced_precondition','priced_offer_checkout_unobserved'):return 'priced_precondition'
 if v=='priced_checkout_observed':return 'checkout_observed'
 if v=='priced_login_required':return 'registration_gate'
 if v in ('partner_lead','affiliate_lead'):return 'partner_lead'
 if v=='external_tuition':return 'adjacent_monetization'
 if v in ('adjacent_tuition','adjacent_application','adjacent_exam','application_fee','adjacent_application_fee'):return 'adjacent_monetization'
 if 'adjacent' in v or 'adjacent' in x.get('verification','').lower():return 'adjacent_content'
 if 'cart' in v:return 'buy_cta_only'
 if 'priced' in v or 'paid' in v and ('lead' in v or 'checkout' in v):return 'priced_lead'
 if 'result' in v and 'free' in v:return 'free_result_observed'
 if 'lead' in v or 'contact' in v:return 'public_lead'
 if 'blocked' in v or 'limited' in v:return 'access_limited'
 if 'official' in v or 'free_human' in v:return 'official_free_channel'
 if 'next' in v or 'handoff' in v:return 'public_referral'
 return 'public_answer' if x.get('free') else 'access_limited'
for r in raw_routes:
 group=clean_host(r.get('host') or pu(r.get('entry')).hostname)
 entry=exact_url(r['entry']); exact_rows=exact.get(entry,[])
 if exact_rows:
  poss=Counter(x['PROJECT_ID'] for x in exact_rows).most_common()
  if group not in {k for k,n in poss}:group=poss[0][0]
  scope='exact_included_url'
 elif group in projects and projects[group]['keys']:
  scope='additional_route_of_corpus_project'
 else:scope='external_benchmark'
 if 'adjacent' in r.get('verification','').lower() or r.get('scope','').startswith('adjacent'):
  if not exact_rows:scope='adjacent_or_excluded'
 proj=projects[group];proj['routes'].append(r['id']);titles.setdefault(group,r['project'])
 mechanism=label_payment(r)
 source_content_with_adjacent_offer={r['id']} if r.get('scope_free_p08') else set()
 if proj['keys'] and scope!='adjacent_or_excluded' and (mechanism not in ('access_limited','adjacent_content') or r['id'] in source_content_with_adjacent_offer):
  matched_projects.add(group)
 if isinstance(r.get('sources'),str):r['sources']=[r['sources']]
 provider=r.get('recipient') or r['project'];
 # A listed provider is not verification of a checkout's legal payment recipient.
 row={
  'PATH_ID':r['id'],'PROJECT_ID':group,'DOMAIN':group,'PROJECT_NAME':r['project'],'REGION':r['market'],'SCOPE':scope,
  'CLUSTERS_HINT':'|'.join(sorted({keys[o['query_id']]['CLUSTER_BASE_ID'] for o in exact_rows})),
  'ENTRY_URL':r['entry'],'FINAL_URL':r.get('next_url',''),'CTA_NATIVE':r.get('cta',''),'CTA_RU':r.get('cta_ru',''),
  'ACCESS_OR_INPUTS':r.get('limits',''),'FREE_OUTCOME':r.get('free',''),'PAID_PRODUCT':r.get('paid',''),
  'PRICE':r.get('price',''),'PUBLIC_PROVIDER':provider,'VERIFIED_PAYMENT_RECIPIENT':'','MONETIZATION':mechanism,
  'PAYMENT_MODEL_RAW':r.get('payment_type',''),'VERIFICATION':r.get('verification',''),
  'EVIDENCE_URLS':' | '.join(x for x in r.get('sources',[]) if isinstance(x,str)), 'LIMITS':r.get('limits',''),
  'SCREENSHOT_IDS':'','EXACT_LINKED_KEYS':len({o['query_id'] for o in exact_rows}),
 }
 paths.append(row);report_routes.append({**r,'exact_scope':scope,'exact_keys':row['EXACT_LINKED_KEYS']})
 for o in exact_rows:
  links.append({'PATH_ID':r['id'],'OBSERVATION_ID':o['observation_id'],'QUERY_ID':o['query_id'],'PROJECT_ID':o['PROJECT_ID'],'MATCH_BASIS':'Одинаковый адрес посадочной после нормализации схемы, www и завершающего слеша. Параметры запроса сохранены.'})
 for i,s in enumerate(r.get('steps',[]),1):
  if isinstance(s,str):s={'outcome':s}
  steps.append({'PATH_ID':r['id'],'STEP_ID':r['id']+'.'+str(i),'STEP_NO':i,'URL':s.get('url') or r['entry'],
   'ELEMENT':s.get('element') or s.get('screen') or s.get('step') or '', 'CTA_NATIVE':s.get('cta',''),
   'NEXT_ACTION':s.get('next_url') or s.get('next') or '', 'OUTCOME':s.get('outcome') or s.get('result') or s.get('description') or '',
   'PRICE':s.get('price',''), 'PUBLIC_PROVIDER':provider, 'EVIDENCE_URL':s.get('url') or r['entry'],'VERIFICATION':s.get('status') or r.get('verification','')})
step_lookup=defaultdict(list)
for s in steps:step_lookup[s['PATH_ID']].append(s)
shots=[]; shot_links=[]; seen=set(); route_shots=defaultdict(list)
for m in sorted([*W.glob('*shots.csv'), *W.glob('*_screenshots.csv')]):
 for record in read_csv(m):
  rid=record.get('route_id') or record.get('PATH_ID') or record.get('route')
  image=record.get('path') or record.get('file') or record.get('filename') or record.get('relative_path')
  url=record.get('url') or record.get('current_url') or record.get('URL') or routes_by_id.get(rid,{}).get('entry','')
  proof=record.get('proof') or record.get('claim') or record.get('observation') or record.get('description')
  if not rid or rid not in routes_by_id or not image: raise ValueError((m,record))
  f=W/image
  if not f.is_file():raise FileNotFoundError(f)
  with Image.open(f) as img:
   slug=re.sub(r'[^a-z0-9-]','-',f.stem.lower().replace('_','-'))
   ident=record.get('screenshot_id') or rid+'-'+slug
   if ident in seen: continue
   seen.add(ident)
   original=Path('screenshots/originals')/(ident+('.png' if img.format=='PNG' else '.jpg'))
   (O/original).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,O/original)
   jpeg=Path('screenshots/html')/(ident+'.jpg');(O/jpeg).parent.mkdir(parents=True,exist_ok=True)
   if img.format=='JPEG':shutil.copy2(f,O/jpeg)
   else:img.convert('RGB').save(O/jpeg,quality=93,optimize=True)
   requested_step=record.get('step_no')
   matches=[s for s in step_lookup[rid] if requested_step and str(s['STEP_NO'])==requested_step]
   matches=matches or [s for s in step_lookup[rid] if exact_url(s['URL'])==exact_url(url)] or step_lookup[rid][:1]
   sid=matches[0]['STEP_ID'] if matches else ''
   shots.append({'SCREENSHOT_ID':ident,'PATH_ID':rid,'STEP_ID':sid,'URL':url,'CAPTURED_AT':record.get('captured_utc') or DATE,'LOCALE':record.get('language') or '', 'DEVICE':record.get('device') or 'Браузер',
   'STATE':'Публичный экран','PIXELS':f'{img.width} × {img.height}','PROVES':proof or 'Публичный экран маршрута','ORIGINAL':str(original),'HTML_JPEG':str(jpeg)})
  route_shots[rid].append(ident);shot_links.append({'SCREENSHOT_ID':ident,'PATH_ID':rid,'STEP_ID':sid})
for r in paths:r['SCREENSHOT_IDS']='|'.join(route_shots[r['PATH_ID']]);
for name,data in [('pathways',paths),('steps',steps),('path_observations',links),('screenshots',shots),('screenshot_links',shot_links)]:write_csv(name,data)
write_json(T/'pathways_input.json',report_routes)
site_rows=[]; land_rows=[]
for group,pj in sorted(projects.items(),key=lambda item:(-len(item[1]['keys']),item[0])):
 site_rows.append({'PROJECT_ID':group,'DOMAIN':group,'NAME':titles.get(group,'Домен не установлен' if group.startswith('unresolved-sha-') else group),'STATUS':'домен не установлен: один массив под разными именами' if group.startswith('unresolved-sha-') else 'есть интерфейсное свидетельство' if group in matched_projects else 'реестр доступности URL, без доказанного маршрута' if pj['keys'] else 'нет принятых ключей исходного корпуса',
  'SOURCE_FILES':len(pj['sources']),'SOURCE_FOLDERS':'|'.join(sorted(filter(None,pj['folders']))),'OBSERVATIONS':pj['obs'],'QUERY_KEYS':len(pj['keys']),
  'SOURCE_DOMAINS':'|'.join(sorted(filter(None,pj['nominals']))),'P08_LANDING_URLS':len(pj['landings']),'ROUTES':len(pj['routes']),
  'SCREENSHOTS':sum(len(route_shots[r]) for r in pj['routes'])})
observed_urls={exact_url(r['ENTRY_URL']) for r in paths if exact_url(r['ENTRY_URL'])}
for (group,domain,host,url),l in sorted(landings.items(),key=lambda it:(-len(it[1]['keys']),str(it[0]))):
 status='not_addressable' if not url else 'reader_not_attempted'; x=reader.get(url) or reader_norm.get(exact_url(url));
 if x:status=x['status']
 if exact_url(url) in observed_urls:status='route_reviewed'
 land_rows.append({'PROJECT_ID':group,'nominal_domain':domain,'landing_host':host,'target_url':url,'source_regions':'|'.join(sorted(l['regions'])),
 'included_keys':len(l['keys']),'families':'|'.join(sorted(l['clusters'])),'PAGE_ROLE':'страница из выгрузки','PAGE_ROLE_BASIS':'Поиск связан по наблюдению, действие доказано только в реестре маршрутов',
 'PUBLIC_CHECK':status,'VERIFIED_CURRENT_URL':(x or {}).get('current_url',''), 'PUBLIC_TITLE':(x or {}).get('title',''), 'PUBLIC_PROBE_NOTE':(x or {}).get('error','') or ('Публичное чтение не выполнено: адрес не относится к безопасному HTTP(S) входу либо параметры содержат чувствительное поле' if status=='reader_not_attempted' else 'В исходной строке отсутствует URL' if status=='not_addressable' else '')})
write_csv('projects',site_rows);write_csv('landings',land_rows)
source_rows=[]
for s in source_inventory:
 akeys=by_file[s['source_id']];source_rows.append({**s,'included_observations':len(akeys),'included_keys':len({o['query_id'] for o in akeys})})
write_csv('source_coverage',source_rows)
for s in source_rows:
 regions[s['region']]
region_rows=[{'Папка источника':r,'Ключи':len(p['keys']),'Наблюдения':p['obs'],'Проекты':len(p['sites']),'Выгрузки':sum(s['region']==r for s in source_rows)} for r,p in sorted(regions.items())];write_csv('regions',region_rows)
market_rows=[{'Поисковик':e,'Поисковый рынок':m,'Язык':l,'Ключи':len(p['keys']),'Наблюдения':p['obs']} for (e,m,l),p in sorted(markets.items(),key=lambda x:(-len(x[1]['keys']),x[0]))];write_csv('markets',market_rows)
cluster_rows=[{'Кластер':i,'Задача':task,'Название':name,'Ключи':sum(q['CLUSTER_BASE_ID']==i for q in keys.values())} for i,(task,name) in FAMILIES.items()];write_csv('clusters',cluster_rows)
write_csv('cluster_markets',[{'Кластер':c,'Намерение':i,'Рынок':m,'Язык':l,'Поисковик':e,'Метрика':t,'Ключи':len(ids)} for (c,i,m,l,e,t),ids in sorted(cluster_markets.items())])
covered={r['PROJECT_ID'] for r in site_rows if r['QUERY_KEYS']>0}
meta.update({'candidate_counts':dict(Counter(r['decision'] for r in judged)),'included_observations':len(obs),'raw_unique':len({o['query_raw'] for o in obs}),
 'project_rows_included':len(covered),'project_rows_total':len(site_rows),'project_rows_with_evidence':len(matched_projects),
 'v4_source_files':len(source_rows),'files_with_hits':sum(s['included_keys']>0 for s in source_rows), 'folder_hits':sum(row['Ключи']>0 for row in region_rows),
 'market_count':len({o['search_market'] for o in obs if o['search_market']}),'languages':dict(Counter(k['LANGUAGE'] for k in keys.values())),
 'accepted_landings':len(exact),'paths':len(paths),'exact_routes':sum(r['SCOPE']=='exact_included_url' for r in paths),'unique_source_hashes':len(hash_domains),'ambiguous_hashes':len(ambiguous_hashes),
 'shots_paths':sum(bool(v) for v in route_shots.values()),'steps':len(steps),'screenshots':len(shots),'by_d':dict(count_d),'subgroups':len(cluster_markets),
 'by_family':{r['Кластер']:r['Ключи'] for r in cluster_rows if r['Ключи']},'cluster_names':{k:f[1] for k,f in FAMILIES.items()},
 'route_scopes':dict(Counter(r['SCOPE'] for r in paths)),'reader_attempts':sum(x['status']!='reader_not_attempted' for x in reader.values()),'reader_readable':sum(x['lines']>0 for x in reader.values()),
 'trial_date':DATE,'route_query_edges':len(links), 'highlights': load(W/'highlights.json')})
meta['candidate_counts']['included']=len(keys)
write_json(T/'coverage.json',meta)
assert len(source_rows)==meta['scanned_files']
assert len(keys)==len({o['query_id'] for o in obs})
assert all(x['QUERY_ID'] in keys for x in links)
print(json.dumps(meta,ensure_ascii=False,indent=2))
