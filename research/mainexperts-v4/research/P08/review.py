"""Classify current regulatory lookup, related criteria and separately observed intent."""
import argparse
import csv
import re
from collections import Counter
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidates',type=Path)
p.add_argument('output',type=Path)
p.add_argument('--register-keys',type=Path)
a=p.parse_args()
register_keys=set(a.register_keys.read_text().splitlines()) if a.register_keys else set()

def rx(s):return re.compile(s,re.I)
ADJACENT=rx(r"\banabin\b|\bzab\b|\bwes\b|学信网|學信網|学历认证|学历查询|(?:verify|verification of|check|recognition of).{0,14}(?:my|your|foreign) (?:degree|diploma|certificate)|(?:degree|diploma|credential|certificate) (?:verification|evaluation|attestation|apostille|equivalen)|(?:attestation|apostille|evaluation|equivalen).{0,12}(?:degree|diploma|credential)|провер.{0,20}(?:диплом|аттестат).{0,16}(?:подлиннос|реестр|номер)|апостил|нострификац|трудов.{0,15}лицензи")
PROVIDER_PROCESS=rx(r"how to (?:get|become|obtain|apply for).{0,26}(?:licen[cs]|accredit)|(?:licen[cs]ing|accreditation) (?:process|application|requirements for providers)|(?:fees for|fees to) (?:accredit|licen[cs])|как (?:получить|оформить|пройти|продлить).{0,24}(?:лицензи|аккредитац)|получение лицензии на образовательн|лицензия.{0,18}документы для получен")
NON_ED=rx(r"\b(?:driver|pilots?|aircraft|gaming|alcohol|restaurant|car dealer|software|plumbing|ngo|bonds?|sandbox|construction|plumber|insurance|notary|forklift)\b.{0,28}(?:licen[cs]|accredit)|(?:licen[cs]|accredit).{0,28}\b(?:driver|pilots?|aviation authority|gaming|alcohol|software|insuranc|notary)\b|кредитна[яе] лицензи|аттестация сотрудник|лицензия.{0,15}(?:пилот|нотариус|алкогол|охот)|\bcollege of [a-z]+ of ontario.*licen[cs]")
MARKER=rx(r"accredit|аккредит|лицензи|licen[cs]|recognised|recognized|рекоменд|recognized|approved|statut|autoriz|agr[ée]|anerkannt|akkredit|认可|認可|合法资质|認證|معترف|معتمد|اعتماد")
LIST=rx(r"\b(?:best|top|cheap(?:est)?|most affordable|list of|all)\b.{0,25}(?:accredited|licensed)|\b(?:accredited|licensed)\b.{0,20}\b(?:online|schools|institutions|universities|providers|programs|programmes)\b|\b(?:online|international)\b.{0,21}(?:accredited|licensed)|аккредитованны[ех] (?:вузы|вузов|колледж[еи]|программ)|مؤسسات.{0,14}معتمدة")
CHECK=rx(r"\b(?:is|are|was|were|does|check|verify|status)\b|проверк|проверить|проверя|как узнать|имеет ли|есть ли|статус|наличие|v[ée]rifi|comproba|verifica|كيف|التحقق|查詢|查询")
EXACT_IDS=rx(r"(?:по|зная) (?:инн|огрн|номеру|коду)|(?:licen[cs]e|registry|registration|course|provider).{0,20}(?:verifi|check|lookup|search).{0,15}(?:by (?:id|number|code)|tool)|(?:check|verify|lookup|look up).{0,18}(?:licen[cs]e|registration|course|provider).{0,18}(?:by (?:id|number|code)|with |number|code)|сервис проверки лицензии|проверка аккредитации онлайн|\b(?:accreditation|licen[cs]e|recognition) (?:checker|verification tool|status check tool)\b|^cricos\s*\d+[a-z]?$")
PAID=rx(r"(?:\b(?:order|buy|pay for|paid|price of|fee for)\b|заказ[а-я]*|купить|(?<!бес)платн[а-я]*|цен[аыу]|стоимость|prix|tarif|preis|kosten).{0,27}(?:accreditation status check|formal accreditation verification|licen[cs]e verification report|проверк.{0,20}(?:лицензи.{0,10}(?:вуз|школ|образоват)|аккредитации (?:программы|вуза)))|(?:accreditation status check|formal accreditation verification|проверка аккредитации программы).{0,18}(?:price|fee|стоимость|цена|prix|kosten)")
DOC=rx(r"(?:registry extract|official extract|official status letter|выписк[аеиу].{0,30}(?:лицензи|аккредитац)|официальн.{0,12}справк[ау].{0,18}статус)")
CRICOS_CODE=rx(r"\bcricos\b.{0,34}(?:code|number)|(?:code|number).{0,25}\bcricos\b|^cricos\s*\d+")
REGISTER=rx(r"\b(?:register|registry|directory|database|search|ruct|dapip|deqar|rncp|cricos)\b|реестр|(?:liste|r[ée]pertoire).{0,24}(?:formations|certifications|accredit)|名冊|名册|قائمة")
ACRONYMS=rx(r"^(?:caa|rncp|ruct|of[fs]|teqsa|chea|cricos|deqar|dapip|training\.gov\.au|qualifications register)$")

def resolve(r):
    q=r['query_normalized']; prior=r['prior_cluster']; resolved=r['lexical_cluster'] or r['cluster']
    if NON_ED.search(q) or r['resolution']=='excluded':
        return 'exclude',resolved,'','','Лицензия или статус вне образовательного объекта'
    if ADJACENT.search(q):
        return 'adjacent',resolved,'','','Верификация или признание уже выданной личной квалификации (P13)'
    if re.search(r'можно ли работать.{0,42}без аккредитац|получил[а]?.{0,18}диплом.{0,18}без аккредитац',q):
        return 'adjacent',resolved,'','','Уже выданный диплом или допуск к профессии (P13/P19)'
    if r['language']=='fr' and re.search(r'\blicence\b',q) and not re.search(r'accr[ée]dit|reconn|habilit|autoris|visa|grade de|statut',q):
        return 'adjacent',resolved,'','','Licence во французском запросе обозначает степень или программу (P02/P04/P11)'
    if re.search(r'^(?:online )?(?:aacsb |aba |bacp )?accredited (?:online )?(?:mba|sonography|nursing|law|business)\b',q) and not CHECK.search(q) and r['query_id'] not in register_keys:
        return 'adjacent',resolved,'','','Каталожный подбор с критерием аккредитации (P06/P07)'
    if re.search(r'(?:應用學習|应用学习).{0,15}(?:認可|认可)',q):
        return 'adjacent',resolved,'','','Признание результатов обучения, применение результата к поступлению (P09/P13)'
    if PROVIDER_PROCESS.search(q):
        return 'adjacent',resolved,'','','Получение или продление лицензии организацией, процесс провайдера'
    if ACRONYMS.search(q) and r['query_id'] not in register_keys and not (prior=='K031' and r['is_direct'].lower()=='true'):
        return 'ambient',resolved,'','','Неоднозначное название реестра; профильный URL отсутствует'
    if re.fullmatch(r'проверить аккредитацию|как проверить аккредитацию|staatlich anerkannt|dipl[oô]me vis[ée]',q) and r['query_id'] not in register_keys and not r['is_direct'].lower()=='true':
        return 'ambient',resolved,'','','Общий запрос получил бы статус P08 только с профильным наблюдением'
    if re.search(r'military (?:friendly|accredited) colleges',q):
        return 'adjacent',resolved,'','','Выбор учреждения для военнослужащих (P06/P18)'
    if re.search(r'\bdli\b',q) and re.search(r'colleges?|universit|designated|approved|list|schools?',q):
        return 'accept','K031','D1','I12','Запись DLI для образовательной мобильности; вторично P16, предел схемы учтён'
    if re.search(r'\bap courses\b.*approved by college board',q):
        return 'accept','K029','D1','I04','Авторизация AP по схеме College Board (Q08.02a), без вывода об учреждении'
    if resolved=='K135' or CRICOS_CODE.search(q):
        lookup=bool(EXACT_IDS.search(q) or re.search(r'\bcode (?:lookup|search|checker)\b|(?:lookup|look up) (?:cricos )?code',q))
        return 'accept','K135','D2' if lookup else 'D1','I07' if lookup else 'I04','Сопоставление кода или номера CRICOS с объектом'
    if PAID.search(q):
        return 'accept',resolved,'D3','I10','Явный запрос цены или заказа отдельной платной проверки статуса'
    if resolved.startswith('P08-'):
        return 'accept',resolved,'D1','I04','Объект, дата, охват или изменение регуляторной записи'
    if DOC.search(q):
        return 'accept',resolved,'D2','I08','Готовый документ по статусу образовательного объекта'
    if EXACT_IDS.search(q) and not re.search(r'^как|^how\b|^what\b',q) and (r['query_id'] in register_keys or re.search(r'учеб|образоват|вуз|университет|колледж|школ|accredit|educat|course|program|univer|college',q)):
        return 'accept',resolved,'D2','I07','Запрос формы, поля или проверка по идентификатору'
    if resolved=='K031' or (REGISTER.search(q) and r['query_id'] in register_keys):
        if REGISTER.search(q) or MARKER.search(q) or r['query_id'] in register_keys:
            return 'accept','K031','D1','I12','Поиск конкретного реестра или списка регулируемых объектов'
    if resolved in ('K029','K030'):
        if LIST.search(q) and not CHECK.search(q) and r['query_id'] not in register_keys:
            return 'adjacent',resolved,'','','Подбор или рейтинг с критерием аккредитации (P06/P07); P08 вторично'
        if MARKER.search(q):
            return 'accept',resolved,'D1','I04','Установить статус конкретного объекта либо смысл образовательной аккредитации'
    if prior in ('K029','K030','K031','K135') and (r['is_direct'].lower()=='true') and MARKER.search(q):
        return 'accept',prior,'D1','I04','Исходная метка подтверждена термином статуса'
    return 'ambient',resolved,'','','Утрачен контекст статуса или исходный URL не подтверждает неоднозначное намерение'

with a.candidates.open(encoding='utf-8-sig',newline='') as src,a.output.open('w',encoding='utf-8',newline='') as dst:
    writer=csv.writer(dst)
    writer.writerow(('query_id','decision','cluster','evidence','intent','note'))
    counts=Counter()
    for row in csv.DictReader(src):
        result=resolve(row)
        counts[result[:3]]+=1
        writer.writerow((row['query_id'],*result))
    for rule,count in sorted(counts.items()):print(*rule,count,sep='\t')
