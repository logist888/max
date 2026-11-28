"""Review P06 catalog and personal-selection signals with separate provenance."""
import argparse
import csv
import re
from collections import Counter
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
def rx(p):return re.compile(p,re.I)

off=rx(r'каникул|школьн\w* календар|расписани\w* (?:занят|урок)|calendario escolar|school holidays|подборовская школа|menedzher-po-podboru-personala|school term dates|holiday dates|public holidays|cursos de verano.{0,18}(?:jobs|empleo)')
ranking=rx(r'\brankings?\b|рейтинг|\btop\b.{0,45}(?:college|universit|school|degree|program)|\bbest\b.{0,45}(?:college|universit|schools?|degree|program)|лучши\w*.{0,38}(?:вуз|колледж|университ|школ|программ)|mejores universidades|classement des|meilleures? univers|\bvs\b|compare.{0,22}(?:college|universit|program)|сравни\w*.{0,24}(?:вуз|университ|программ)')
admin=rx(r'what is|definition|meaning|что такое|как поступить в|entry requirements|score required|application deadline|when to apply|набор.*срок|пр[ои]ходн\w* балл|документ\w* для поступ|lettre de motivation|推荐信|推薦信|перевестись|перевод в другой вуз|que son los ciclos|вакансии|job description|salary|зарабатыва|обязанности|номер телефон|регистрац\w* лиценз|правила при[её]м')
brand=rx(r'официальный сайт|\bwebsite\b|\blogin\b|\bsign in\b|личный кабинет|школа (?:номер |№)?\d|^госуслуги подбор|^iu fernstudium$')
definition=rx(r'^(?:(?:bachelor(?: s)?|masters?|master s|undergraduate|graduate|postgraduate|associate|doctoral) degree(?:s)?|магистратура|бакалавриат|аспирантура|высшее образование|licence|mba|phd|bachelor|master)$')
personal=rx(r'\b(?:match quiz|matching tool|college quiz|college match|school matching|university matching|degree matching|program(?:me)? matching|finder quiz|recommendation tool|personaliz\w*|personalis\w*|tailored|for me|should i|based on my|my gpa|my grades|my profile|my scores|my interests|my budget|for my child|passt zu mir)\b|(?:подбор|подобрать).{0,33}(?:по баллам|по предметам|по критериям|под меня|индивидуальн|персональн|по успеваемости|под бюджет)|(?:по баллам|по предметам|индивидуальн|персональн).{0,29}(?:подбор|подобрать)|test.{0,22}(?:quelle formation|universit[ée] pour moi)|选校名单|選校名單|(?:大学|大學|院校).{0,7}(?:匹配|推荐|推薦)|اختيار.{0,20}(?:الجامعة المناسبة|البرنامج المناسب)')
direct_pay=rx(r'(?:(?:стоимость|цен[ау]|заказать|купить|платн\w*|тариф).{0,28}(?:подбор\w*|шорт лист|коротк\w* список)|(?:подбор\w*|шорт лист|коротк\w* список).{0,28}(?:стоимость услуг|цен[ау] услуг|платн\w*|заказать)|(?:paid|pay for|book|hire|price of|cost of|buy).{0,30}(?:college list building|college matching|university matching|school search service|personalized program(?:me)? shortlisting)|(?:college list building|college matching|university matching|school search service).{0,20}(?:price|pricing|service fee))')
personal_named=rx(r'^what (?:college|school|university) should i (?:go to|apply to|choose)|^какой вуз (?:мне выбрать|мне подойд[её]т)')
generic_kind=rx(r'^(?:college|colleges|university|universities|schools?|институт\w*|вуз\w*|университет\w*|колледж\w*|школ\w*)$')
catalog_school=rx(r'(?:universit\w*|colleges|schools|hochschul\w*|universit[ée]\w*|universidad\w*) .{0,6}(?:in|near|en|around|für|pour|par|of) .+|(?:вуз\w*|университет\w*|колледж\w*|школ\w*) (?:в |для |с |по |недалеко |рядом |после )|(?:near me|by state|по регионам|каталог|lista de|elenco|annuaire|список|найти|искать|such[eé]|ricerca)|(?:public|private|international|boarding) (?:universities|colleges|schools)|(?:государственн\w*|частн\w*|международн\w*) (?:вуз\w*|колледж\w*|школ\w*)')
catalog_landing=rx(r'(?:/college-search|/colleges(?:/|$)|/universities(?:/|$)|/search(?:/|\?)|/region/|/geo/|/etablissements/|/find-a-course|/sitemap)')
catalog_program=rx(r'(?:online|part time|distance|blended|full time|affordable|accredited|free) .{0,37}(?:degree|program|course|master|bachelor)|(?:masters?|bachelor|phd|programmes?|programs?|courses?) .{0,6}(?:in|en|for|near|to become) .+|(?:заочн\w*|дистанц\w*|онлайн|вечерн\w*|онлайн|очно заочн\w*).{0,32}(?:магистратур|бакалавриат|образован|программ)|(?:курс\w*|программ\w*|магистратур\w*|бакалавриат\w*).{0,40}(?:онлайн|заочн|дистанц|бесплатн|в москв|на английск|после 9|после 11)|(?:поиск|каталог|найти|список|trouver|studiengangsuche|buscador|ricerca)')
catalog_program_landing=rx(r'/search/|/programmy-obucheniya|/find-a-course|/courses(?:$|/)|/for-abiturients/')
reasons={
'K023':'Подбор вариантов по параметрам человека. Доказательность зависит от формулировки.',
'K024':'Каталог организаций по типу, месту или иному критерию.',
'K025':'Поиск подходящих программ по категории или формату.',
'K114':'Поиск профессиональной или прикладной программы.',
'K115':'Поиск внешкольного, короткого или летнего формата.',
'K125':'Поиск программы обмена, мобильности или международного курса.',
'K140':'Поиск по направлению, уровню или формату.',
'P06-K30':'Запрос на составление персонального короткого списка.'
}

def decide(row):
    q=row['query_normalized']; u=row['target_url']; c=row['cluster']
    if off.search(q) or 'menedzher-po-podboru-personala' in u:
        return 'exclude',c,'','Расписание, подбор персонала или совпадение с именем вне задачи подбора образования.'
    if c=='K023' and re.match(r'^(?:what degree should i (?:get|choose|do) (?:quiz|test)|what career should i choose)',q,re.I) and re.search(r'career',u,re.I):
        return 'adjacent',c,'','Профориентация по направлению или профессии — P01.'
    if c not in reasons:
        return 'residual',c,'','Предмет требует отдельной проверки.'
    if ranking.search(q):
        return 'adjacent',c,'','Рейтинг, сравнение или оценка качества — смежный сценарий P07.'
    if admin.search(q) or definition.fullmatch(q):
        return 'adjacent',c,'','Справка о ступени, факт поступления, визы, карьера или отдельная административная задача.'
    if brand.search(q):
        return 'ambient',c,'','Навигация к известной организации или инструменту; не прямой сигнал нового подбора.'
    if c in ('K023','P06-K30'):
        if direct_pay.search(q):
            return 'accept',c,'D3','Коммерческий модификатор относится к услуге подбора.'
        if personal.search(q) or personal_named.search(q) or c=='P06-K30' or rx(r'college (?:fit quiz|quiz match)|(?:вуз\w*|университет\w*) .{0,10}по (?:баллам|предметам) егэ|quale universit[àa] scegliere (?:quiz|test)').search(q):
            return 'accept',c,'D2',reasons[c]
        return 'accept',c,'D1','Поиск подбора, параметры результата и готовность платить не установлены.'
    if c=='K024' and not (catalog_school.search(q) or catalog_landing.search(u) and re.search(r'(?:^colleges?$|^universities$|школы|вузов|колледжи|университеты|universit[ée]s|\bcolleges? in\b)',q,re.I)) or c=='K024' and generic_kind.fullmatch(q):
        return 'ambient',c,'','Название организации или общий тип. Явный критерий подбора не установлен.'
    if c=='K025' and not (catalog_program.search(q) or catalog_program_landing.search(u) and re.search(r'program|bachelor|master|курс|программ',q,re.I)):
        return 'ambient',c,'','Название программы или ориентир без выраженного критерия каталожного подбора.'
    if c=='K125' and re.search(r'\b(?:funding|scholarships?)\b|положени\w* об обмене',q,re.I):
        return 'adjacent',c,'','Финансирование или правила обмена, без поиска вариантов.'
    return 'accept',c,'D1',reasons[c]

with a.source.open(encoding='utf-8-sig',newline='') as f,a.output.open('w',encoding='utf-8',newline='') as out:
    w=csv.writer(out); w.writerow(['query_id','decision','cluster','evidence','note']); count=Counter()
    for row in csv.DictReader(f):
        result=decide(row);w.writerow([row['query_id'],*result]);count[result[:3]]+=1
print(count)
