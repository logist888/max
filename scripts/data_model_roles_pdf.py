#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Бриф для C-level по модели данных docs/10-data-model.md.
One-pager на роль: CEO / COO / CMO / CPO / CTO. Дизайн — как плейбук:
A4, поля 20 мм, DejaVu Sans, палитра бренда, рисованная схема, critic-блок.
Рендер: WeasyPrint. Выход: Модель_данных_бриф_для_C-level.pdf
"""
import os
from weasyprint import HTML

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "vault", "40-reports", "playbook-otzyvy"))
PDF_NAME = "Модель_данных_бриф_для_C-level.pdf"

PRIMARY="#1D4ED8"; SECONDARY="#0F172A"; ACCENT="#10B981"; WARNING="#F59E0B"
ERROR="#DC2626"; INDIGO="#4338CA"; CYAN="#0891B2"; INK="#1E293B"; MUTED="#64748B"
LINE="#E2E8F0"; BG="#F8FAFC"

CSS=f"""
@page {{ size:A4; margin:20mm 20mm 18mm 20mm;
  @bottom-left {{ content:"Бриф для C-level · Модель данных MainExperts";
    font-family:'DejaVu Sans'; font-size:7.5pt; color:{MUTED}; }}
  @bottom-right {{ content:counter(page); font-family:'DejaVu Sans'; font-size:8.5pt;
    font-weight:bold; color:{SECONDARY}; }}
}}
@page cover {{ margin:0; @bottom-left{{content:none}} @bottom-right{{content:none}} }}
*{{box-sizing:border-box}}
html{{font-family:'DejaVu Sans',sans-serif}}
body{{margin:0;color:{INK};font-size:11pt;line-height:1.42}}
p{{margin:0 0 6pt 0}}
strong{{color:{SECONDARY}}}
h1,h2,h3{{margin:0;color:{SECONDARY};line-height:1.15}}

.cover{{page:cover;height:297mm;position:relative;color:#fff;
  background:radial-gradient(1100px 480px at 80% -10%,rgba(16,185,129,.32),transparent 60%),
  linear-gradient(150deg,{SECONDARY} 0%,#16265c 48%,{PRIMARY} 100%);overflow:hidden}}
.cover .frame{{position:absolute;inset:14mm;border:1px solid rgba(255,255,255,.22)}}
.cover .in{{position:absolute;inset:32mm 32mm}}
.cover .eyebrow{{letter-spacing:.4em;font-size:11pt;text-transform:uppercase;color:rgba(255,255,255,.72);margin-bottom:8mm}}
.cover .kick{{display:inline-block;font-size:9.5pt;letter-spacing:.26em;text-transform:uppercase;
  color:{ACCENT};border:1px solid rgba(16,185,129,.5);padding:3pt 10pt;border-radius:20pt;margin-bottom:12mm}}
.cover h1{{color:#fff;font-size:37pt;line-height:1.08;margin:0 0 6mm;letter-spacing:-.5pt}}
.cover .sub{{font-size:13.5pt;color:rgba(255,255,255,.86);max-width:150mm;line-height:1.5}}
.cover .aud{{position:absolute;left:32mm;right:32mm;bottom:40mm;display:flex;flex-wrap:wrap;gap:6pt}}
.cover .chip{{font-size:9pt;color:#fff;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.22);
  border-radius:16pt;padding:4pt 11pt}}
.cover .meta{{position:absolute;left:32mm;right:32mm;bottom:24mm;font-size:8.5pt;color:rgba(255,255,255,.6);
  border-top:1px solid rgba(255,255,255,.2);padding-top:5mm;display:flex;justify-content:space-between}}
.cover .wm{{position:absolute;right:-30mm;top:150mm;font-size:150pt;font-weight:bold;color:rgba(255,255,255,.05)}}

.page{{break-before:page}}
.eyebrow{{font-size:8.5pt;letter-spacing:.22em;text-transform:uppercase;font-weight:bold;margin-bottom:4pt}}
.rt{{font-size:26pt;font-weight:bold;letter-spacing:-.3pt}}
.rt small{{font-size:13pt;color:{MUTED};font-weight:normal;letter-spacing:0}}
.lead{{font-size:12.5pt;color:{MUTED};margin:6pt 0 4pt;max-width:150mm}}
.rule{{height:4pt;border-radius:3pt;margin:9pt 0 12pt;width:70mm}}

.blk{{border:1px solid {LINE};border-radius:9pt;background:#fff;padding:10pt 13pt;margin-bottom:9pt}}
.blk .h{{font-size:8.5pt;font-weight:bold;letter-spacing:.1em;text-transform:uppercase;margin-bottom:4pt}}
.blk p{{margin:0;font-size:10.5pt;line-height:1.44;text-align:justify}}

.chips{{margin:2pt 0 10pt}}
.chips .c{{display:inline-block;font-size:8.5pt;background:{BG};border:1px solid {LINE};
  border-radius:14pt;padding:3pt 9pt;margin:0 4pt 5pt 0;color:{INK};font-family:'DejaVu Sans'}}
.chips .lbl{{font-size:8pt;letter-spacing:.08em;text-transform:uppercase;color:{MUTED};margin-right:5pt}}

.border{{background:#FEF2F2;border:1px solid {ERROR};border-left:5pt solid {ERROR};
  border-radius:8pt;padding:10pt 13pt;margin-top:3pt}}
.border .h{{font-weight:bold;color:{ERROR};font-size:10pt;margin-bottom:3pt}}
.border p{{margin:0;font-size:10pt;line-height:1.42;text-align:justify}}

.intro h2{{font-size:20pt;padding-bottom:5pt;border-bottom:2.5pt solid {PRIMARY};margin-bottom:9pt}}
.intro .big{{font-size:13pt;line-height:1.5;color:{SECONDARY};background:linear-gradient(180deg,#fff,{BG});
  border:1px solid {LINE};border-left:6pt solid {ACCENT};border-radius:8pt;padding:12pt 15pt;margin-bottom:12pt}}
figure{{margin:6pt 0 12pt}}
.schema{{border:1px solid {LINE};border-radius:10pt;background:#fff;padding:12pt}}
.schema svg{{width:100%;height:auto;display:block}}
figcaption{{font-size:8.5pt;color:{MUTED};margin-top:7pt;padding-top:6pt;border-top:1px dashed {LINE}}}
.two{{display:table;width:100%;border-spacing:9pt;margin:0 -9pt}}
.two .col{{display:table-cell;width:50%;vertical-align:top}}
.callout{{border-radius:8pt;padding:10pt 12pt;border:1px solid;font-size:10pt;line-height:1.42;height:100%}}
.c-imp{{background:#FFFBEB;border-color:{WARNING}}}
.c-imp .h{{font-weight:bold;color:#92400E;margin-bottom:2pt}}
.c-note{{background:#EFF4FF;border-color:{PRIMARY}}}
.c-note .h{{font-weight:bold;color:{PRIMARY};margin-bottom:2pt}}
"""

def spine_svg():
    nodes=[("Product",PRIMARY),("SKU",PRIMARY),("Listing",INDIGO),("Market × Channel",SECONDARY),("Fact",ACCENT)]
    W,gap=150,26; xs=[15+i*(W+gap) for i in range(5)]; y=26; h=52
    s=[f'<svg viewBox="0 0 {xs[-1]+W+15} 120" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    lays=[("Ядро",PRIMARY,15,xs[2]-10),("Рынок×Канал",SECONDARY,xs[3]-8,W+16),("Факт",ACCENT,xs[4]-8,W+16)]
    for x,(label,color) in zip(xs,nodes):
        s.append(f'<rect x="{x}" y="{y}" width="{W}" height="{h}" rx="11" fill="#fff" stroke="{color}" stroke-width="2"/>')
        s.append(f'<rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{color}"/>')
        s.append(f'<text x="{x+W/2+3:.0f}" y="{y+h/2+5:.0f}" fill="{SECONDARY}" font-size="13" font-weight="bold" text-anchor="middle">{label}</text>')
    for i in range(4):
        ax=xs[i]+W; s.append(f'<path d="M{ax},{y+h/2:.0f} H{xs[i+1]-4}" stroke="{MUTED}" stroke-width="2"/>')
        s.append(f'<path d="M{xs[i+1]-4},{y+h/2-5:.0f} l7,5 l-7,5 Z" fill="{MUTED}"/>')
    # подпись слоёв снизу
    s.append(f'<text x="15" y="100" fill="{MUTED}" font-size="10">Слой 0–1: справочники, локализация, цены, налоги</text>')
    s.append(f'<text x="{xs[3]-8}" y="100" fill="{MUTED}" font-size="10">Слой 3: append-only факты</text>')
    s.append('</svg>')
    return "".join(s)

ROLES=[
 dict(color=SECONDARY, tag="Основатель · CEO", name="Основатель", en="CEO",
   lead="Единый язык компании: цель → факт → решение, а не графики.",
   blocks=[
    ("Что это для вас","Один источник истины. Продукт, рынок, цена, продажа и цель живут в связанной модели, а не в головах и разрозненных файлах. Вы видите цепочку «цель → факт → решение», а не набор графиков."),
    ("Что вы держите","Верх дерева целей и <strong>правило двух потоков</strong>, реализованное физически — разрезом по каналу и базовой валюте. Поток-1 (₽/£, личные продажи) и поток-2 (воронка) <strong>не сводятся в одной витрине</strong>. Это свойство схемы, а не декларация."),
    ("Какие решения включает","Куда направлять деньги (P&amp;L по продукту, рынку, каналу); какие гипотезы закрыты; выполняется ли план. Модель — тот самый Data Dictionary, которого не хватало бордам: она их и питает."),
   ],
   chips=["business_objectives","правило двух потоков","P&L сводно","дерево целей"],
   border="Это <strong>спецификация, а не работающая база</strong> — данных пока нет. Строить сложную модель раньше выручки — риск преждевременной сложности (тот же, что с бордами). Гипотеза скрининга остаётся <strong>ставкой</strong>: модель её проверит через test_objectives, но сама не подтвердит."),
 dict(color=ACCENT, tag="Операционный директор · COO", name="Операционный директор", en="COO",
   lead="Все операционные события в одном месте и append-only.",
   blocks=[
    ("Что это для вас","Заказы, возвраты, подписки, брони, остатки — в одном фактовом слое. Ничего не редактируется задним числом: корректировка всегда новая строка (возврат — отдельная запись, а не удаление исходной)."),
    ("Что вы держите","Фактовый слой: order_lines, subscriptions (период = строка: старт → продление → отмена), bookings (услуги), inventory_snapshots. Витрина <strong>«недели запаса»</strong> — раннее предупреждение о дефиците."),
    ("Какие решения включает","Хватает ли товара под темп продаж; где рвётся SLA услуг; как ведёт себя отток подписок — без ручной сверки версий и файлов."),
   ],
   chips=["order_lines","inventory_snapshots","subscriptions","bookings","недели запаса"],
   border="Остатки живут на грани <strong>SKU × склад</strong>, а не листинга (сток общий) — «недели запаса по листингу» считаются разложением. Модель <strong>не про мощность экспертов</strong>: узкое место проекта (ручная проверка отчёта) — это борд Operations, модель его не заменяет."),
 dict(color=PRIMARY, tag="Директор по маркетингу · CMO", name="Директор по маркетингу", en="CMO",
   lead="Расход честно соединён с выручкой; ни одной метрики свободным текстом.",
   blocks=[
    ("Что это для вас","Каждый KPI — запись в словаре с формулой из фактов. ROAS и ДРР считаются <strong>после комиссии канала и налога</strong>, а не по «грязной» выручке. Метрик «на глаз» в системе не существует."),
    ("Что вы держите","Слой целей: campaign / channel / test objectives. Baseline и target — <strong>числами с датами</strong>, не текстом. План живёт в целях, факт — в outcomes и витринах; в одной ячейке они не смешиваются."),
    ("Какие решения включает","Какой канал прибылен; где план против факта красный; достиг ли тест порога и какое решение принято. Атрибуция связывает заказ с кампанией."),
   ],
   chips=["kpi_definitions","campaign_objectives","channel_objectives","outcomes"],
   border="Атрибуция — <strong>одно касание (last-click)</strong>: мульти-тач вне модели, для длинного цикла принятия это упрощение. Правило потоков жёсткое: публичное соц. доказательство воронки нельзя подмешивать к приватной премиальной экономике."),
 dict(color=INDIGO, tag="Директор по продукту · CPO", name="Директор по продукту", en="CPO",
   lead="Каталог, запускающий что угодно и где угодно без переделки схемы.",
   blocks=[
    ("Что это для вас","Продукт не знает о ценах и языках — они живут ниже, на листинге и рынке. Новый вариант, продукт, рынок или канал = <strong>новые строки, ноль структурных изменений</strong> (доказано сценариями приёмки 2 и 3)."),
    ("Что вы держите","Ядро Product → SKU → Listing + локализация (карточка на N языков без дублей SKU) + подписки как жизненный цикл. На вашу номенклатуру ложится прямо: Free / Pro / Ultima и Профиль 10 / 360 — это SKU и листинги; премиум-услуги (визы, релокация) — отдельные SKU."),
    ("Какие решения включает","Что масштабировать по марже (P&amp;L сводно по продукту); как ведут себя тарифы и подписки; как дёшево локализовать на новый рынок."),
   ],
   chips=["products","skus","listings","listing_content","subscriptions"],
   border="Модель — про <strong>каталог и коммерцию, не про продуктовый опыт</strong>: квиз, цифровой профиль и AI-отчёт она не описывает (это платформа на Rust). Себестоимость цифровых SKU номинальна — юнит-экономику подписки надо докрутить реальными затратами."),
 dict(color=CYAN, tag="Технический директор · CTO", name="Технический директор", en="CTO",
   lead="Нормализованная спецификация: строгие FK, append-only, история цен.",
   blocks=[
    ("Что это для вас","31 таблица, человекочитаемые ID, append-only факты, история цен через price_periods (заказ ссылается на период, действовавший в момент продажи). <strong>Ноль дублирования</strong>: цена — только в ценовых периодах, контент — в локализации, комиссия — в экономике канала."),
    ("Что вы держите","Всю схему. Ключевые инженерные решения уже приняты и обоснованы: налог — таблицей с датами (ставка на дату факта); себестоимость — периодическим справочником; грань остатков — SKU × склад."),
    ("Какие решения включает","Путь внедрения: сегодня — связанные таблицы (Sheets / Airtable / Notion), завтра — перенос на платформу Rust один-в-один (ядро и слой целей — те же сущности). Базовая валюта — конфиг <strong>на поток</strong>, не глобальная константа."),
   ],
   chips=["31 таблица","append-only","price_periods","fx_rates","строгие FK"],
   border="Хрупкое — два места: <strong>полиморфные ссылки</strong> (objective_scope, outcomes на «любую цель» через тип+ID) разъезжаются без валидации; <strong>валютный слой</strong> — все витрины зависят от fx_rates на дату. Это спецификация, не БД: индексов, констрейнтов и ETL нет — вводить при переносе (раздел ETL/Security Тома II — пробел)."),
]

def build():
    B=[]
    B.append(f"""
<div class="cover"><div class="frame"></div><div class="wm">10</div>
  <div class="in">
    <div class="eyebrow">MainExperts · docs/10</div>
    <div class="kick">Бриф для C-level</div>
    <h1>Модель данных:<br/>запуск любого<br/>продукта где угодно</h1>
    <div class="sub">Как одна реляционная модель — от бизнес-цели до ежедневного факта —
      выглядит с пяти управленческих кресел. Что она даёт именно вам и где её честная граница.</div>
  </div>
  <div class="aud">
    <span class="chip">CEO · Основатель</span><span class="chip">COO · Операции</span>
    <span class="chip">CMO · Маркетинг</span><span class="chip">CPO · Продукт</span>
    <span class="chip">CTO · Технологии</span>
  </div>
  <div class="meta"><div>Внутренний документ · рабочий контекст, не выверенный источник</div>
    <div style="text-align:right">08.07.2026 · Конфиденциально</div></div>
</div>""")

    # интро
    B.append(f"""
<section class="page intro">
  <div class="eyebrow" style="color:{PRIMARY}">Модель в одном предложении</div>
  <h2>Единый источник истины — от цели до факта</h2>
  <div class="big">Единая реляционная модель, где <strong>план и факт разведены</strong>, а
    <strong>каждая цифра раскладывается до формулы</strong> из фактовых таблиц. Она запускает любой
    продукт (физический, цифровой, услугу, подписку) на любом рынке, языке, в любой валюте и на
    любом канале — и управляет этим запуском от бизнес-цели до ежедневного факта.</div>
  <figure><div class="schema">{spine_svg()}<figcaption><strong>Ядро онтологии.</strong>
    Продукт не знает о ценах и языках; факты ссылаются на листинг, а не на продукт напрямую —
    иначе теряется атрибуция канала и рынка.</figcaption></div></figure>
  <div class="two">
    <div class="col"><div class="callout c-imp"><div class="h">Сквозное правило · два потока</div>
      Поток-1 (Founder Premium, ₽/£) и поток-2 (воронка) консолидируются только на уровне
      собственника; ниже — своя экономика. Метрики потоков <strong>не объединять</strong> —
      в модели это разрез по каналу и базовой валюте.</div></div>
    <div class="col"><div class="callout c-note"><div class="h">Сквозная правда · стадия</div>
      Это <strong>спецификация, а не работающая БД</strong>. Ценность сейчас — единый язык и
      готовый каркас (Data Dictionary, которого не хватало бордам), к которому идём по мере
      появления данных, а не немедленный бэклог.</div></div>
  </div>
</section>""")

    for r in ROLES:
        blocks="".join(
            f'<div class="blk" style="border-left:4pt solid {r["color"]}">'
            f'<div class="h" style="color:{r["color"]}">{h}</div><p>{t}</p></div>'
            for h,t in r["blocks"])
        chips='<span class="lbl">Объекты, которыми вы управляете</span>' + "".join(
            f'<span class="c">{c}</span>' for c in r["chips"])
        B.append(f"""
<section class="page">
  <div class="eyebrow" style="color:{r['color']}">{r['tag']}</div>
  <div class="rt">{r['name']} <small>· {r['en']}</small></div>
  <div class="lead">{r['lead']}</div>
  <div class="rule" style="background:{r['color']}"></div>
  {blocks}
  <div class="chips">{chips}</div>
  <div class="border"><div class="h">Честная граница</div><p>{r['border']}</p></div>
</section>""")

    return "<!doctype html><html lang='ru'><head><meta charset='utf-8'><style>"+CSS+"</style></head><body>"+"".join(B)+"</body></html>"

def main():
    os.makedirs(OUT_DIR,exist_ok=True)
    doc=build()
    open(os.path.join(OUT_DIR,"roles-source.html"),"w",encoding="utf-8").write(doc)
    pdf=os.path.join(OUT_DIR,PDF_NAME)
    HTML(string=doc,base_url=OUT_DIR).write_pdf(pdf)
    print("PDF:",pdf,os.path.getsize(pdf),"bytes")

if __name__=="__main__":
    main()
