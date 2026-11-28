"""Adjudicate P03 candidates using explicit boundaries and preserve every decision."""
import argparse
import csv
import re
from collections import Counter
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()

def expr(pattern):return re.compile(pattern,re.IGNORECASE)
formal=expr(r'аккредит|лицензи|accredit|recognized institution|reconocid[ao]|staatliche anerkennung|认证大学|認證大學|recognised degree')
operator=expr(r'\bинн\b|\bогрн\b|реквизит|учредител|юридическ\w* лиц|legal entity|company number|registered company|legal operator|who owns|кому принадлежит|siret|raison sociale|rechtsträger|ente gestore|法人|信用代码|运营主体|السجل التجاري|الكيان القانوني')
commercial=expr(r'(?:заказ(?:ать| проверки)|оплатить|стоимость (?:аудита|проверки)|цен[ау] (?:аудита|проверки)|нанять|\b(?:buy|pay for|hire|commission|order)\b.{0,35}(?:proof|audit|check|due diligence|verification)|(?:audit|due diligence|verification|background check) (?:cost|price|service fee))')
fee_admission=expr(r'стоимость обучен|цен[ау] обучен|адрес[аы] и цен[аыу]|цены и адрес|платно[е й]|tuition|admission fee|стоимость поступлен|проходно\w* балл|вступительн|правила прием|как поступить|admission requirements|бакалавриат стоимость|бюджетн\w* мест')
program=expr(r'специальност|направлени\w* подготов|programmes|degree programs|course catalogue|что сдавать|какие предметы|what to study')
contact=expr(r'электронн\w* (?:почт|адрес)|почтовый индекс|номер телефон|official site|официальный сайт|телефон\w* при[её]м|email address|e mail address|email list|форма связи')
review=expr(r'отзыв|рейтинг|reputation|ratings|feedback|top best|хороший ли|хорош\w* вуз')
job=expr(r'ваканси|зарплат|резюме|требования к преподавател|бюджетник|зарабатыва|сколько получают|обязанност|career as|hiring|\bearn\b|\bsalary\b|дефицит|медсправк|повышени\w* квалиф|устроиться|размер ставк')
complaint=expr(r'жалоб|жаловаться|комплаенс|complaint|поскандал')
generic=expr(r'^(?:факультет\w* (?:вуза|вузов|университета|университетов|института)|преподавател\w* вуз\w*|faculty members|teacher directory|campus map|адрес (?:университета|вуза|колледжа))$')
search_category=expr(r'^(?:diploma mills?|fake universities|diploma mills? (?:meaning|definition|examples)|what is a diploma mill|is college a scam|野鸡大学|野雞大學)$')
training=expr(r'(?:\b(?:middle|high|graduate|secondary|primary|trade) school\b.{0,25}(?:list|near me)|^spider man|^what is not part of a college application|^which item is not part of a college application)')
faculty_definition=expr(r'факультет\w* .{0,30}(?:это|что такое|как понять)|(?:что такое|что означает) факультет')
simple_operator=expr(r'директор школы (?:это|юридическ)|(?:как найти|как узнать) (?:свой|своего)')
award_general=expr(r'di maturità|диплом (?:о среднем|школьный)')
address=expr(r'(?:адрес|расположен|находится|location|where is|map|campus|地址|地圖|地图|adresse|ubicación|indirizzo|عنوان)')

reasons={
 'K009':'Кампус, корпус или физический адрес образовательной организации.',
 'K010':'Подразделение или связь филиала с конкретной организацией.',
 'K011':'Состав преподавателей или профиль участника; рейтинг и отзывы отделены.',
 'K012':'Проверка существования, идентичности или подлинности образовательного оператора.',
 'K129':'Реквизиты, учредитель или идентификация юридического участника.',
 'P03-K13':'Подтверждение состояния работы площадки.',
 'P03-K14':'Установление организации, присуждающей квалификацию.',
 'P03-K15':'Установление собственника или принадлежности к группе.',
 'P03-K16':'Расшифровка полного или официального имени организации.',
}

def decide(row):
 q=row['query_normalized'].lower(); c=row['cluster']
 if c not in reasons:return 'residual', c, '', 'Требует дополнительной разметки кластера.'
 if training.search(q):return 'exclude',c,'','Нецелевое совпадение или поиск класса организаций.'
 if formal.search(q):return 'adjacent',c,'','Формальное право, лицензия, аккредитация или признание — P08/P13.'
 if complaint.search(q):return 'adjacent',c,'','Обращение или жалоба — отдельный процесс P21.'
 if c in ('K009','K010') and review.search(q):return 'adjacent',c,'','Отзывы и репутация относятся к P07.'
 if c=='K009' and expr(r'юридическ\w* адрес|registered office').search(q):return 'accept','K129','D1','Юридический адрес оператора, отдельно от места обучения.'
 if c=='K011' and (review.search(q) or job.search(q)):return 'adjacent',c,'','Отзывы и оценка — P07; работа и требования к преподавателю — P19.'
 if c=='K012' and expr(r'(?:fake university (?:degree|certificate|diploma)|фальшивый диплом)').search(q):return 'adjacent',c,'','Подлинность документа — отдельная ветвь P13.'
 if c=='K129' and (simple_operator.search(q) or expr(r'^школа (?:это )?юридическое лицо$').fullmatch(q)):return 'adjacent',c,'','Определение статуса должности или учебный вопрос без конкретной организации.'
 if c=='P03-K13' and expr(r'закрытие сессии|сесси\w* закры').search(q):return 'adjacent',c,'','Речь об учебной сессии, а не работе площадки.'
 if c=='P03-K14' and award_general.search(q):return 'adjacent',c,'','Общее правило системы без конкретной присуждающей организации — P02/P13.'
 if c=='K010' and (faculty_definition.search(q) or expr(r'(?:разница|чем отлича)').search(q) and expr(r'факультет').search(q)):return 'adjacent',c,'','Понятие подразделения без идентификации организации — справка P02.'
 if c=='K009' and contact.search(q) and not expr(r'кампус|campus|где наход|where is|physical address|street address').search(q):return 'adjacent',c,'','Контакт, сайт или почтовый индекс без физической идентификации — навигация или P21.'
 if c in ('K009','K010') and (fee_admission.search(q) or program.search(q) and c=='K010'):
  return 'adjacent',c,'','Преобладает цена, поступление или каталог программ — P14/P09/P06; сохранено как смежное.'
 if c in ('K009','K010','K011') and generic.fullmatch(q):return 'adjacent',c,'','Общее понятие без названия участника или различимой площадки.'
 if c=='P03-K15' and 'college board' in q:return 'exclude',c,'','College Board — организация стандартизированных экзаменов, вне выбранного типа образовательного объекта.'
 if row['resolution'] in ('review_prior_label','review_secondary'):
  if c=='K009' and address.search(q):return 'accept',c,'D1',reasons[c]
  if c=='K010' and expr(r'факультет|подразделени|филиал|department|facult[éaà]|fachbereich').search(q):return 'accept',c,'D1',reasons[c]
  if c=='K011' and not expr(r'^преподаватель вуза$|^преподаватели вузов$|^преподаватели в вузах$|^преподаватель университета$|^как стать|^кто такой').search(q) and expr(r'преподавател|профессор|faculty|enseignant|师资').search(q):return 'accept',c,'D1',reasons[c]
  return 'residual',c,'','Метка v4 есть, но предмет запроса не подтверждён независимым правилом.'
 if c=='K012' and search_category.fullmatch(q):return 'accept',c,'D1','Общая информационная формулировка об идентификации или подлинности; не запрос об отдельной организации.'
 level='D3' if c in ('K012','K129','P03-K13','P03-K15') and commercial.search(q) else 'D1'
 return 'accept',c,level,reasons[c]

with a.source.open(encoding='utf-8-sig',newline='') as source, a.output.open('w',encoding='utf-8',newline='') as output:
 writer=csv.writer(output);writer.writerow(['query_id','decision','cluster','evidence','note']); totals=Counter()
 for row in csv.DictReader(source):
  result=decide(row);writer.writerow([row['query_id'],*result]);totals[(result[0],result[1],result[2])]+=1
print(totals)
