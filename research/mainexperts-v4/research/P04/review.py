"""Adjudicate P04 query candidates without inferring the requested object from its landing alone."""
import argparse
import csv
import re
from collections import Counter
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()

def rx(pattern):
    return re.compile(pattern,re.I)

resume=rx(r'curr[ií]culum vitae|bewerbung.{0,15}lebenslauf|\blebenslauf\b|\bresume (?:template|sample|examples?|writing)\b|\b(?:cv|curriculum) (?:template|modelo|ejemplo|format|online|vitae)\b|(?:como|cómo|come) (?:hacer|fare|scrivere|creare|elaborar|redactar).{0,35}curr[ií]culum|curriculum dello studente|come si fa.{0,18}curriculum|/curriculum\.html|/trabajar/busqueda/activa\.html|curriculum.{0,18}(?:sin experiencia|lavoro|para trabajar)|sae modificar curriculum|datos para un curriculum|cv\.html|/lebenslauf-erstellen|curriculum-vitae-cv/')
other_meaning=rx(r'master of puppets|\bdungeon master\b|master of disguise|master of none|master of the universe|master of ceremony|\bbachelor (?:party|in paradise)\b|bachelor reality|bachelor of the year|master of the air|master of orion|master of magic')
admission=rx(r'пр[ои]ходн\w* балл|как поступить|условия поступлен|экзамен[ыа] для поступлен|entry requirements|atar (?:requirements?|score|cut.?off)|acceptance rate|how to apply|nota (?:de )?corte|conditions? d admission|bewerbungsfrist|requirements for admission')
price=rx(r'стоимость (?:обучения|программы)|оплата обучен|tuition|course price|scholarship|стипенд|student finance|placement year (?:salary|calculator)|paid (?:for )?(?:(?:a|the) )?placement year|placement year (?:get |is )?paid|placement year jobs|salary after|salaire|что за зарплата')
career=rx(r'débouchés|debouches|berufsaussichten|career opportunities|job prospects|кем работать|куда устроиться')
selector=rx(r'\bbest\b|лучшие|top\s*\d|ranking|рейтин|programs? near me|curriculum.{0,18}schools (?:in|near)|online programs|где учиться|где изучать|список вузов|which university')
document=rx(r'(?:recognition|nostrification|apostille|recognised|accreditation|accredited|признан|нострифика|аккредит|апостил).{0,35}(?:диплом|degree|program|программ)|(?:диплом|degree|program|программ).{0,30}(?:accreditation|accredited|аккредит|нострифика|recognition)')
curriculum=rx(r'учебн\w* план\w*|траектор\w* курса|предметы.{0,18}(?:специальност|бакалавриат)|curr[ií]cul[uo]|syllabus|course structure|module |handbook|degree checklist|degree map|рабоч\w* программ|maquette|piano didattico|m[oó]dulos optativos|studienverlaufsplan|课程设置|課程設置|contents? of|plan de estudios|piano di stud|planes de estudio|modulhandbuch|studienverlaufsplan|programme (?:des cours|de formation)|培养方案|課程')
delivery=rx(r'кто (?:составляет|утверждает)|как (?:создать|составить|написать) (?:учебный план|plan de estudios)|disena-tu-plan-estudio|time management|репетиторств.{0,55}с чего начать')
direct_audit=rx(r'(?:заказ(?:ать| аудита)|цена аудита|стоимость (?:аудита|проверки)|оплатить|hire|commission|book|pay for|price of|fees for).{0,36}(?:аудит|экспертиз|провер|independent review|audit|evaluation|syllabus review)|(?:аудит|audit|independent review).{0,48}(?:cost|price|purchase|цен[ау]|стоимость|заказ)')
narrow_provider=rx(r'\b(?:вшэ|мгу|рудн|спбгу|ранхигс|мит|оксфорд|оксфордский|кембридж|harvard|oxford|cambridge|stanford|sydney|melbourne|toronto|monash|sorbonne|bocconi|eth|epfl|ntu|nus|smu|ucl|imperial|umass)\b|\b(?:université|university of|universidad de|universit[aà] di|hochschule|lycée)\b')
generic_k113=rx(r'^(?:mba|master|masters|licence|licence professionnelle|bachelor|bachelor of (?:science|arts|engineering|commerce|pharmacy)|master of (?:science|arts|business administration)|какое образование|магистратура|бакалавриат|специалитет|degree programs?)$')
course_landing=rx(r'/(?:program/\d|studies/\d|course/\d|cours/\d|programm\w*/\d)|/programmy-obucheniya[^/]+/[^/]+|/(?:undergraduate|graduate|study|degrees?|programmes?)/(?:courses/)?[^/]+/(?:overview|curriculum|course-structure)')
institution_landing=rx(r'^(?:https?://)?(?:[^/]+\.)?(?:edu|ac\.uk|edu\.au|edu\.sg)(?:/|$)|^https?://[^/]+\.(?:edu|ac\.uk|edu\.au|edu\.sg)/')

def decide(row):
    q=row['query_normalized']; url=row['target_url']; c=row['cluster']
    if resume.search(q) or c=='K013' and resume.search(url) or other_meaning.search(q):
        return 'exclude',c,'','Резюме, музыка или иное употребление термина.'
    if c not in {'K013','K014','K015','K016','K113','K130','P04-K17','P04-K18'}:
        return 'residual',c,'','Нужна дополнительная разметка.'
    if c=='K130':
        return 'accept',c,'D3' if direct_audit.search(q) else 'D1','Явный анализ содержания или соответствия образовательной программы.'
    if admission.search(q) or price.search(q) or career.search(q) or selector.search(q) or document.search(q):
        return 'adjacent',c,'','Первичный результат относится к допуску, стоимости, поиску/оценке вариантов, признанию или карьере.'
    if c=='K013':
        if delivery.search(q) or delivery.search(url):
            return 'adjacent',c,'','Разработка собственного расписания учёбы или управление программой.'
        if not curriculum.search(q):
            return 'residual',c,'','Исходная метка есть; содержание запроса не подтверждено явным признаком.'
        if q in {'curriculum','plan de estudios','piano di studi'} and not re.search(r'/curriculum|/piano-di-studi|/plan-de-estudios',url,re.I):
            return 'residual',c,'','Краткий многозначный запрос; адрес недостаточен для установления задачи.'
        return 'accept',c,'D1','Запрос учебного плана или структуры; проверяемая версия устанавливается по первичному документу.'
    if c=='K113':
        if generic_k113.fullmatch(q) or not narrow_provider.search(q):
            return 'ambient',c,'','Название типа / направления программы либо ранний поиск. Конкретная версия по запросу не подтверждена.'
        return 'accept',c,'D1','Идентификация программы с названным учреждением. Версия и точность посадочной всё равно требуют сверки.'
    if c=='K014':
        return 'accept',c,'D1','Поиск кода или классификатора. Код описывает категорию; программа и версия плана проверяются отдельно.'
    if c=='K015':
        return 'accept',c,'D1','Двойная или совместная программа; нужно установить структуру и присуждающие организации.'
    if c=='K016':
        return 'accept',c,'D1','Роль встроенной практики или года стажировки. Оплата практиканта относится к отдельному сценарию.'
    return 'accept',c,'D1','Явное уточнение результатов, обязательных дисциплин или условий завершения.'

with a.source.open(encoding='utf-8-sig',newline='') as source,a.output.open('w',encoding='utf-8',newline='') as output:
    writer=csv.writer(output); writer.writerow(['query_id','decision','cluster','evidence','note']); totals=Counter()
    for row in csv.DictReader(source):
        result=decide(row); writer.writerow([row['query_id'],*result]); totals[(result[0],result[1],result[2])]+=1
print(totals)
