"""Add reusable official, navigation, and continuation routes without a product."""
import csv
from pathlib import Path

CONFIG=Path(__file__).resolve().with_name("config")
ROUTES = (
    ("C-neutral-official","I15","E03","official_route","/methods/{destination}/{cluster}/","Перейти к официальному источнику",
     "Показать порядок действий","Проверить актуальные условия или оплатить обязательный сбор внешней организации",
     "official_page","Публичный порядок, правила и известный получатель платежа",
     "external_party","Ссылка на подтверждённый источник","official_resource_opened","Доля открытий проверенного источника"),
    ("C-neutral-nav","I12","E06","entity","/entities/{destination}/{entity}/","Открыть карточку",
     "Перейти на официальный сайт","Известно, какой объект искал пользователь","entity_profile",
     "Карточка объекта и официальный URL",None,"Открытая карточка","entity_opened","Доля открытий нужного объекта"),
    ("C-neutral-resume","I14","E23","resume","/account/resume/","Продолжить действие",
     "Открыть официальный кабинет","Пользователь возвращается к уже начатому процессу","resume_or_official_account",
     "Возврат к собственному шагу или ссылка на официальный кабинет",None,"Авторизация только на стороне нужного процесса",
     "journey_resumed","Доля успешных возобновлений"),
    ("C-neutral-answer","I01","E01","guide","/guides/{destination}/{cluster}/","Открыть правила",
     "Найти официальный источник","Есть подтверждённая информационная задача","guide",
     "Применимое правило со ссылкой, датой и условиями",None,"Открытый справочный блок",
     "guide_opened","Доля осмысленных переходов к следующей задаче"),
)
LOCAL = {
  "en":(("Open the official source","See the steps"),("Open the profile","Go to the official website"),("Resume","Open the official portal"),("See the rules","Find the official source")),
  "fr":(("Aller à la source officielle","Voir la démarche"),("Ouvrir la fiche","Accéder au site officiel"),("Reprendre la démarche","Ouvrir le portail officiel"),("Voir les règles","Trouver la source officielle")),
  "de":(("Offizielle Quelle öffnen","Ablauf ansehen"),("Profil öffnen","Offizielle Website öffnen"),("Vorgang fortsetzen","Offizielles Portal öffnen"),("Regeln ansehen","Offizielle Quelle finden")),
  "it":(("Vai alla fonte ufficiale","Vedi la procedura"),("Apri la scheda","Vai al sito ufficiale"),("Riprendi la procedura","Apri il portale ufficiale"),("Vedi le regole","Trova la fonte ufficiale")),
  "es":(("Ir a la fuente oficial","Ver los pasos"),("Abrir la ficha","Ir al sitio oficial"),("Continuar el trámite","Abrir el portal oficial"),("Ver los requisitos","Buscar la fuente oficial")),
  "ar":(("افتح المصدر الرسمي","عرض الخطوات"),("عرض الملف","افتح الموقع الرسمي"),("متابعة الإجراء","افتح البوابة الرسمية"),("عرض القواعد","ابحث عن المصدر الرسمي")),
  "zh-Hans":(("查看官方来源","查看办理流程"),("查看详情","访问官方网站"),("继续办理","打开官方平台"),("查看规则","查找官方来源")),
  "zh-Hant":(("查看官方來源","查看辦理流程"),("查看詳情","前往官方網站"),("繼續辦理","開啟官方平台"),("查看規則","尋找官方來源")),
}
def build():
    with (CONFIG/"conversions.tsv").open(encoding="utf-8",newline="") as f:
        fields=next(csv.reader(f,delimiter="\t"))
    records=[]
    translations=[]
    for idx, r in enumerate(ROUTES):
        key,intent,element,page,url,primary,secondary,trigger,target,free,payment,fulfil,event,kpi=r
        records.append(dict(CONVERSION_ID=key,ROUTE_KIND="official" if key.endswith("official") else "free",
          INTENT_ID=intent,PAGE_TYPE=page,PAGE_URL_PATTERN=url,ELEMENT_ID=element,CTA_PRIMARY=primary,CTA_SECONDARY=secondary,
          CTA_TRIGGER=trigger,CTA_TARGET=target,FREE_VALUE=free,PAYMENT_TYPE=payment,FULFILMENT=fulfil,EVENT=event,KPI=kpi,
          CTA_PLACEMENT="Первый блок после идентификации задачи",TARGET_ACTION=target,INPUTS="Контекст запроса и выбранный объект",
          TEST_METHOD="Проверка целевого ресурса и наблюдение за успешным переходом"))
        for lang,pair in [("ru",(primary,secondary)),*((k,v[idx]) for k,v in LOCAL.items())]:
            translations.append([key,lang,*pair,primary,secondary])
    with (CONFIG/"neutral_conversions.tsv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fields,delimiter="\t");w.writeheader();w.writerows(records)
    with (CONFIG/"neutral_cta_localizations.tsv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t");w.writerow(["CONVERSION_ID","LANGUAGE","CTA_PRIMARY","CTA_SECONDARY","CTA_PRIMARY_RU","CTA_SECONDARY_RU"]);w.writerows(translations)
if __name__=="__main__":
    build()
