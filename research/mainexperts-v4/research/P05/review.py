"""Adjudicate P05 intake and deadline candidates while retaining adjacent Q05 properties."""
import argparse
import csv
import re
from collections import Counter
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()

def rx(pattern):return re.compile(pattern,re.I)

finance=rx(r'financial aid|student finance|\bfafsa\b|\bcss profile\b|scholarship|bourse étudiant|bourse etudiant|\bdse\b|стипенд|финансов\w* помощ')
exam=rx(r'\b(?:sat|act|gre|gmat|lsat|mcat|ielts|toefl|ap exam|exam)\b.{0,23}(?:registr|application|date|deadline)|(?:date|deadline|registr\w*|application) .{0,20}\b(?:sat|act|gre|gmat|lsat|mcat|ielts|toefl|exam)\b|регистрац\w* на (?:экзамен|егэ|огэ)|\bscore submission deadline\b')
decision=rx(r'(?:(?:r[ée]sultat|r[ée]ponse|admission decision|decision release|waitlist|waiting list|решение о зачислении|когда зачислен|списки зачисленных).{0,28}(?:parcoursup|date|дата|срок)|(?:when do|release of|status of).{0,30}(?:admission decisions|offer results)|check (?:my |your )?application status|отследить статус заявк|replying to (?:an |your )?offer|reply deadline|accept offer deadline|подтвердить согласие на зачисление)')
visa=rx(r'visa|виза|иммиграц|passport|residen[ct] permit')
unrelated=rx(r'fluid intake|water intake|air intake|calorie intake|recruitment for employment|high school musical|\b(?:tax|patent|procurement|grant proposal|immigration lottery|voter)\b')
no_edu=rx(r'(?:^.{0,16}$)|^(?:application deadline|application deadlines|admission deadline|closing date|enrollment deadline)$')
education=rx(r'college|university|universit|school|course|study|grad|degree|bachelor|masters?|phd|enrol|ucas|parcoursup|mon master|common app|\b(?:ntu|nus|hkust|cu hk|hku|smu|ouac|qtac|vtac|uac|jupas)\b|колледж|вуз|университ|институт|поступлен|бакалав|магистр|при[её]мн\w* кампани|образован|обучен|курсы|учебн|inscripci|admisión|candidatur|bewerbung|immatricolaz|iscrizion|入学|入學|招生|التعليم|الدراسة')
edu_landing=rx(r'/(?:admissions?|apply|applying|important-dates|key-dates|deadlines?|enrolment|enrollment|dates-and-deadlines|intakes?|calendrier)(?:/|\b)|parcoursup\.gouv|monmaster\.gouv|ouac\.on\.ca|\bucas\.com')
direct=rx(r'напоминан|уведомлен|отслеживан|мониторинг|\b(?:tracker|alerts?|reminders?|notifications?|monitoring|tracking)\b|rappel|alerte|erinnerung|recordatorio|提醒|تنبيه')
commercial=rx(r'\b(?:buy|paid|subscribe|price|pricing|premium|fee)\b|купить|платн|подписк|цен[ау]|стоимость|abonnement|precio|tarif')
clearing_context=rx(r"\bclearing\b")
clearing_edu=rx(r"\b(?:ucas|uni|university|college|undergraduate)\b|(?:ucas|whatuni|theuniguide|completeuniversityguide|studential)\.")
static_k128=rx(r'^dossier rappel parcoursup$')
date_k047=rx(r'deadline|applications? due|when to apply|при[её]мн\w* кампан|cut.?off|date|calend|frist|termin|scadenza|plazo|срок|дата|до какого|когда|截止|موعد')
reasons={
'K017':'Календарный поток, сезонный или смещённый старт образовательной программы.',
'K018':'Открытие, закрытие или текущая доступность подачи на образовательный набор.',
'K047':'Срок подачи, календарь приёмной кампании или предельная дата для указанной аудитории.',
'K128':'Явный поиск инструмента напоминания или отслеживания сроков.',
'P05-K29':'Дополнительный раунд, поздний вход или возможность податься после основного срока.',
}
def decide(row):
    q=row['query_normalized']; url=row['target_url']; c=row['cluster']
    if c in ('K019','K020','K021'):
        return 'ambient',c,'','Смежные параметры реализации Q05: учебное расписание, длительность или язык. В ядро мониторинга P05 не включены.'
    if c not in reasons:
        return 'residual',c,'','Предмет требует отдельной проверки.'
    if rx(r'parcoursup date de cr[ée]ation|parcoursup founded').search(q):
        return 'exclude',c,'','История площадки, а не календарь приёма.'
    if c=='K017' and rx(r'\bschool start dates?\b').search(q) and not rx(r'intake|enrol|apply|admission').search(q):
        return 'ambient','K019','','Начало учебного периода, отдельно от набора.'
    if c in ('K017','P05-K29') and rx(r'\b(?:intake|clearing) (?:meaning|means)\b|^what is (?:a |the )?(?:intake|clearing)$').search(q):
        return 'ambient',c,'','Определение термина без запроса конкретной даты или действия.'
    if unrelated.search(q):
        return 'exclude',c,'','Необразовательное употребление.'
    if finance.search(q) or exam.search(q) or decision.search(q) or visa.search(q):
        return 'adjacent',c,'','Срок финансирования, экзамена, визы или решения по поданной заявке. Первичная задача вне P05.'
    if c=='P05-K29' and clearing_context.search(q) and not clearing_edu.search(q) and not clearing_edu.search(url):
        return 'residual',c,'','Слово Clearing многозначно без образовательного контекста в запросе или источнике.'
    if c=='K128':
        if static_k128.search(q) or not direct.search(q):
            return 'residual',c,'','Слово rappel встречается в неоднозначной формулировке о досье; настройка отслеживания не установлена.'
        return 'accept',c,'D3' if commercial.search(q) else 'D2',reasons[c]
    if (c=='K047' and not date_k047.search(q)) or (not education.search(q) and not edu_landing.search(url) and no_edu.search(q)):
        return 'residual',c,'','Год, объект или образовательная область недостаточно определены.'
    return 'accept',c,'D1',reasons[c]

with a.source.open(encoding='utf-8-sig',newline='') as f,a.output.open('w',encoding='utf-8',newline='') as out:
    w=csv.writer(out); w.writerow(['query_id','decision','cluster','evidence','note']); count=Counter()
    for row in csv.DictReader(f):
        result=decide(row);w.writerow([row['query_id'],*result]);count[result[:3]]+=1
print(count)
