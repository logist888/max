#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Executive summary GTM-стратегии MainExperts (docs/11) — РЕВИЗИЯ под полную автоматизацию.
Дизайн-грейд PDF: A4, палитра бренда, рисованные схемы. Рендер: WeasyPrint.
Выход: GTM_стратегия_executive_summary.pdf
"""
import os
from weasyprint import HTML

OUT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","vault","40-reports","playbook-otzyvy"))
PDF="GTM_стратегия_executive_summary.pdf"

P="#1D4ED8";S="#0F172A";A="#10B981";W="#F59E0B";E="#DC2626";IN="#4338CA";CY="#0891B2"
INK="#1E293B";M="#64748B";LN="#E2E8F0";BG="#F8FAFC"

CSS=f"""
@page {{ size:A4; margin:18mm 18mm 16mm;
  @bottom-left {{ content:"GTM-стратегия MainExperts · Executive Summary · ревизия под автоматизацию";
    font-family:'DejaVu Sans';font-size:7pt;color:{M}; }}
  @bottom-right {{ content:counter(page);font-family:'DejaVu Sans';font-size:8.5pt;font-weight:bold;color:{S}; }}
}}
@page cover {{ margin:0; @bottom-left{{content:none}} @bottom-right{{content:none}} }}
*{{box-sizing:border-box}} html{{font-family:'DejaVu Sans',sans-serif}}
body{{margin:0;color:{INK};font-size:10.5pt;line-height:1.42}}
p{{margin:0 0 6pt}} strong{{color:{S}}}
h1,h2,h3{{margin:0;color:{S};line-height:1.15}}
.cover{{page:cover;height:297mm;position:relative;color:#fff;
  background:radial-gradient(1100px 460px at 78% -8%,rgba(16,185,129,.3),transparent 60%),
  linear-gradient(150deg,{S} 0%,#14265a 50%,{P} 100%);overflow:hidden}}
.cover .fr{{position:absolute;inset:13mm;border:1px solid rgba(255,255,255,.22)}}
.cover .in{{position:absolute;inset:30mm 30mm}}
.cover .eb{{letter-spacing:.38em;font-size:10.5pt;text-transform:uppercase;color:rgba(255,255,255,.7);margin-bottom:7mm}}
.cover .kk{{display:inline-block;font-size:9pt;letter-spacing:.24em;text-transform:uppercase;color:{A};
  border:1px solid rgba(16,185,129,.5);padding:3pt 10pt;border-radius:20pt;margin-bottom:11mm}}
.cover h1{{color:#fff;font-size:36pt;line-height:1.08;margin:0 0 5mm;letter-spacing:-.5pt}}
.cover .sub{{font-size:13pt;color:rgba(255,255,255,.85);max-width:150mm;line-height:1.5}}
.cover .mt{{position:absolute;left:30mm;right:30mm;bottom:22mm;font-size:8pt;color:rgba(255,255,255,.6);
  border-top:1px solid rgba(255,255,255,.2);padding-top:5mm;display:flex;justify-content:space-between}}
.cover .wm{{position:absolute;right:-20mm;top:150mm;font-size:150pt;font-weight:bold;color:rgba(255,255,255,.05)}}
.sec{{break-before:page}}
.hd{{background:linear-gradient(120deg,{S},{IN});color:#fff;border-radius:11pt;padding:12pt 15pt;margin-bottom:12pt}}
.hd .n{{font-size:8.5pt;letter-spacing:.24em;text-transform:uppercase;color:rgba(255,255,255,.7)}}
.hd h2{{color:#fff;font-size:18pt;margin:3pt 0 0}}
h3{{font-size:12.5pt;color:{P};margin:11pt 0 5pt}}
.lead{{color:{M};font-size:10.5pt;margin-bottom:8pt}}
figure{{margin:9pt 0;break-inside:avoid}} .sch{{border:1px solid {LN};border-radius:9pt;background:#fff;padding:11pt}}
.sch svg{{width:100%;height:auto;display:block}} figcaption{{font-size:8.3pt;color:{M};margin-top:6pt;padding-top:5pt;border-top:1px dashed {LN}}}
.tw{{border:1px solid {LN};border-radius:8pt;overflow:hidden;margin:9pt 0;break-inside:avoid}}
table{{border-collapse:collapse;width:100%;font-size:9pt}}
thead th{{background:{P};color:#fff;text-align:left;padding:6pt 8pt;font-size:8.5pt;border-right:1px solid rgba(255,255,255,.15)}}
thead th:last-child{{border-right:none}}
td{{padding:5.5pt 8pt;border-top:1px solid {LN};vertical-align:top;line-height:1.34}}
tbody tr:nth-child(even){{background:{BG}}} td.k{{font-weight:bold;color:{S}}}
.co{{display:table;width:100%;border-radius:8pt;padding:9pt 12pt;margin:9pt 0;border:1px solid;break-inside:avoid}}
.co .h{{font-weight:bold;font-size:10pt;margin-bottom:2pt}} .co .b{{display:table-cell;font-size:9.5pt;line-height:1.4}}
.c-w{{background:#EFF4FF;border-color:{P}}} .c-w .h{{color:{P}}}
.c-i{{background:#FFFBEB;border-color:{W}}} .c-i .h{{color:#92400E}}
.c-k{{background:#ECFDF5;border-color:{A}}} .c-k .h{{color:#065F46}}
.c-r{{background:#FEF2F2;border-color:{E}}} .c-r .h{{color:{E}}}
.tag{{display:inline-block;font-size:7.5pt;font-weight:bold;padding:1px 6pt;border-radius:4pt;margin-right:3pt}}
.t-f{{background:#D1FAE5;color:#065F46}} .t-o{{background:#DBEAFE;color:#1E40AF}} .t-g{{background:#FEF3C7;color:#92400E}}
ul{{margin:0 0 7pt;padding-left:15pt}} li{{margin-bottom:3pt}}
.big{{font-size:12pt;line-height:1.5;color:{S};background:linear-gradient(180deg,#fff,{BG});
  border:1px solid {LN};border-left:6pt solid {A};border-radius:8pt;padding:11pt 14pt;margin-bottom:10pt}}
"""

def fig(svg,cap): return f'<figure><div class="sch">{svg}<figcaption>{cap}</figcaption></div></figure>'
def co(k,h,b): return f'<div class="co c-{k}"><div class="b"><div class="h">{h}</div>{b}</div></div>'

def automation_svg():
    s=['<svg viewBox="0 0 840 210" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    # smooth funnel, automation box green (no narrowing), constraint moved downstream (conversion)
    steps=[("Трафик",P,180),("Скрининг",P,150),("Регистрация",IN,125)]
    x=15
    for lab,c,h in steps:
        y=(200-h)/2
        s.append(f'<rect x="{x}" y="{y:.0f}" width="110" height="{h}" rx="8" fill="#fff" stroke="{c}" stroke-width="2"/>')
        s.append(f'<text x="{x+55}" y="{100}" fill="{S}" font-size="10" font-weight="bold" text-anchor="middle">{lab}</text>')
        x+=145
    # automation box (green, wide) — no ceiling
    s.append(f'<rect x="{x}" y="62" width="185" height="76" rx="9" fill="#ECFDF5" stroke="{A}" stroke-width="2.4"/>')
    s.append(f'<text x="{x+92}" y="88" fill="#065F46" font-size="10.5" font-weight="bold" text-anchor="middle">АВТОМАТИКА</text>')
    s.append(f'<text x="{x+92}" y="104" fill="#065F46" font-size="9" text-anchor="middle">отчёт + AI-консультант</text>')
    s.append(f'<text x="{x+92}" y="118" fill="#065F46" font-size="9" text-anchor="middle">∞ ёмкость · маржа ~90%</text>')
    x2=x+185+35
    s.append(f'<rect x="{x2}" y="70" width="115" height="60" rx="8" fill="#fff" stroke="{S}" stroke-width="2"/>')
    s.append(f'<text x="{x2+57}" y="104" fill="{S}" font-size="11" font-weight="bold" text-anchor="middle">Оплата</text>')
    # arrows
    for ax in [125,270,415, x+185, x2+115]:
        pass
    for ax in [125,270,415]:
        s.append(f'<path d="M{ax},100 H{ax+30}" stroke="{M}" stroke-width="2"/><path d="M{ax+30},95 l7,5 l-7,5 Z" fill="{M}"/>')
    s.append(f'<path d="M{x+185},100 H{x2-4}" stroke="{M}" stroke-width="2"/><path d="M{x2-4},95 l7,5 l-7,5 Z" fill="{M}"/>')
    # constraint moved: red marker over the reg->pay conversion
    s.append(f'<text x="{x2+57}" y="150" fill="{E}" font-size="9" font-weight="bold" text-anchor="middle">★ новое горлышко:</text>')
    s.append(f'<text x="{x2+57}" y="163" fill="{E}" font-size="9" font-weight="bold" text-anchor="middle">конверсия · доверие</text>')
    s.append(f'<text x="420" y="192" fill="{M}" font-size="9.3" text-anchor="middle">Автоматизация сняла ёмкостный потолок «9–10/день» и ручной фулфилмент. Связывающее ограничение сместилось</text>')
    s.append(f'<text x="420" y="205" fill="{M}" font-size="9.3" text-anchor="middle">с производства на спрос: конвертит ли холодный трафик и доверяет ли клиент продукту без живого эксперта.</text>')
    s.append('</svg>');return "".join(s)

def funnel_svg():
    s=['<svg viewBox="0 0 840 200" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    steps=[("Бюджет","₽20.6 млн",P),("Лиды","80 952",P),("Регистрации","34 000",IN),("Оплаты 50К","1 700",S),("Выручка","$1M",A)]
    W_,g=140,18;xs=[15+i*(W_+g) for i in range(5)];y=40;h=70
    for (t,v,c),x in zip(steps,xs):
        s.append(f'<rect x="{x}" y="{y}" width="{W_}" height="{h}" rx="10" fill="#fff" stroke="{c}" stroke-width="2"/>')
        s.append(f'<rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{c}"/>')
        s.append(f'<text x="{x+W_/2+3:.0f}" y="{y+30}" fill="{M}" font-size="9.5" text-anchor="middle">{t}</text>')
        s.append(f'<text x="{x+W_/2+3:.0f}" y="{y+52}" fill="{S}" font-size="14" font-weight="bold" text-anchor="middle">{v}</text>')
    for i in range(4):
        ax=xs[i]+W_;s.append(f'<path d="M{ax},{y+h/2:.0f} H{xs[i+1]-4}" stroke="{M}" stroke-width="2"/><path d="M{xs[i+1]-4},{y+h/2-5:.0f} l7,5 l-7,5 Z" fill="{M}"/>')
    s.append(f'<text x="420" y="150" fill="{M}" font-size="9.5" text-anchor="middle">Базовый сценарий: конверсия рег→оплата 5% [ГИПОТЕЗА — центральная ставка] · валовая маржа ~89% · ДРР 24%</text>')
    s.append(f'<text x="420" y="168" fill="{A}" font-size="9" text-anchor="middle">Переменная стоимость ≈ 0 (автоматика) → даже высокий ДРР оставляет ~₽55 млн чистой контрибуции. Плюс подписочный LTV.</text>')
    s.append('</svg>');return "".join(s)

def roadmap_svg():
    s=['<svg viewBox="0 0 840 210" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    hs=[("30 дней","Замер конверсии",P),("90 дней","Доверие к ИИ + подписка",IN),("6 мес","Масштаб доказанного",A),("12 мес","Ров + Залив",CY),("24 мес","Актив данных",S)]
    x0,x1=40,800;y=60
    s.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{LN}" stroke-width="3"/>')
    n=len(hs)
    for i,(t,d,c) in enumerate(hs):
        px=x0+(x1-x0)*i/(n-1)
        s.append(f'<circle cx="{px:.0f}" cy="{y}" r="9" fill="{c}"/>')
        s.append(f'<text x="{px:.0f}" y="{y-20}" fill="{S}" font-size="11" font-weight="bold" text-anchor="middle">{t}</text>')
        yy=y+28
        for w in d.split(" + "):
            s.append(f'<text x="{px:.0f}" y="{yy}" fill="{M}" font-size="9" text-anchor="middle">{w}</text>');yy+=13
    s.append(f'<text x="420" y="150" fill="{M}" font-size="9.3" text-anchor="middle">Новое правило: сначала доказать конверсию и доверие к ИИ на холодном трафике →</text>')
    s.append(f'<text x="420" y="166" fill="{M}" font-size="9.3" text-anchor="middle">достроить подписку → масштаб ТОЛЬКО доказанного. Масштабировать до валидации спроса — запрещено.</text>')
    s.append('</svg>');return "".join(s)

FF='<span class="tag t-f">ФАКТ</span>';OO='<span class="tag t-o">ОЦЕНКА</span>';GG='<span class="tag t-g">ГИПОТЕЗА</span>'

def build():
    B=[]
    B.append(f"""
<div class="cover"><div class="fr"></div><div class="wm">$1M</div>
  <div class="in"><div class="eb">MainExperts · docs/11 · ревизия</div><div class="kk">Executive Summary</div>
    <h1>GTM-стратегия:<br/>путь к первому<br/>миллиону долларов</h1>
    <div class="sub">Ревизия под факт основателя: пакет профориентации полностью автоматизирован
      (отчёт + AI-консультант). Узкое место снято — стратегия пересобрана вокруг нового ограничения:
      спроса, конверсии и доверия без человека.</div></div>
  <div class="mt"><div>Внутренний документ · рабочий контекст, не выверенный источник</div>
    <div style="text-align:right">08.07.2026 · Конфиденциально</div></div></div>""")

    B.append(f"""
<section class="sec"><div class="hd"><div class="n">Раздел 1</div><h2>Что изменила автоматизация</h2></div>
  <div class="big">Пакет профориентации <strong>полностью автоматизирован</strong> (отчёт + AI-консультант,
    ручного труда нет). Это опрокидывает прежнюю аксиому «узкое место — ручная проверка». Два следствия:
    ёмкость больше не ограничена, а переменная стоимость единицы схлопнулась к нулю →
    <strong>валовая маржа ~90%</strong>. Объёмная продажа 50К стала не просто возможной, а прибыльной.</div>
  {fig(automation_svg(),'<b>Сдвиг ограничения.</b> Автоматика убрала потолок «9–10/день» и ручной фулфилмент. '
     'Судьбу $1M теперь решают конверсия, спрос и доверие к продукту без живого эксперта — не производственная мощность.')}
  {co('r','Новая центральная ставка (роль критика)',
     '<strong>«AI-консультант заменяет живого эксперта без потери конверсии»</strong> '+GG+' — против собственных '
     'данных проекта: custdev называл эксперта обязательным (8/9), видеозвонок до покупки (7/9). Это не факт, '
     'а ставка уровня гипотезы скрининга. <strong>Проверить на холодном трафике — приоритет №0</strong>, '
     'до любого масштаба.')}
  <h3>Три вопроса спроса, каждый способен убить $1M</h3>
  <div class="tw"><table><thead><tr><th>Ограничение</th><th>Суть</th><th>Как проверить дёшево</th></tr></thead><tbody>
   <tr><td class="k">Конверсия</td><td>конвертит ли холодный трафик рег→оплату</td><td>микро-тест $1500–2000 на 3–5К регистраций</td></tr>
   <tr><td class="k">Доверие к ИИ</td><td>покупает и доволен ли клиент без человека</td><td>A/B: авто vs авто+живой звонок</td></tr>
   <tr><td class="k">Гипотеза скрининга</td><td>оцифровка страха → покупка</td><td>холодный трафик, не тёплый</td></tr>
  </tbody></table></div>
</section>""")

    B.append(f"""
<section class="sec"><div class="hd"><div class="n">Раздел 2</div><h2>Рынки и выбор стратегии</h2></div>
  <h3>Рейтинг рынков</h3>
  <div class="tw"><table><thead><tr><th>#</th><th>Рынок</th><th>Роль</th><th>Почему</th></tr></thead><tbody>
   <tr><td class="k">1</td><td class="k">Россия</td><td>Объём и отладка</td><td>дешёвая итерация; hh.ru {FF}; зрелый спрос; автоматика особенно выигрышна (низкий чек × объём × near-zero стоимость)</td></tr>
   <tr><td class="k">2</td><td class="k">UAE/Залив</td><td>Пилот маржи ($)</td><td>экстремальный WTP {OO} → высокий LTV; но нет данных для отчёта и трафик — ставка</td></tr>
   <tr><td class="k">3</td><td class="k">СНГ</td><td>Дешёвое расширение</td><td>переиспользование почти без затрат</td></tr>
   <tr><td>4–5</td><td>Европа · США</td><td>Отложить</td><td>право на забвение vs бессрочный профиль; COPPA/FERPA + дорогой трафик</td></tr>
  </tbody></table></div>
  <h3>Выбор: основной и резервный сценарий</h3>
  {co('k','S1 — Автоматизированная воронка объёма (ОСНОВНОЙ)',
     'Скрининг → отчёт 50К + AI-консультант → <strong>подписка Pro/Ultima</strong>. Автоматизация сделала его '
     'масштабируемым (нет потолка) и прибыльным (маржа ~90%). ACV растём апселлами и якорением, <strong>не</strong> '
     'принуждая всех к 150К. Раньше основным был S2 (150К) — его смысл (обход ёмкости) исчез.')}
  {co('w','S2 — ACV-tilt (РЕЗЕРВНЫЙ)',
     'Если конверсия на 50К окажется слишком низкой (ДРР недопустим), смещаем микс к дорогим тирам ради '
     'маркетинг-эффективности. S2 теперь — рычаг ДРР, а не побег от ёмкости. Сегмент Ольга (55%) снова главный '
     'объёмный таргет: обслуживать её стало масштабируемо.')}
</section>""")

    B.append(f"""
<section class="sec"><div class="hd"><div class="n">Раздел 3</div><h2>Финансовая модель (пересобрана)</h2></div>
  {fig(funnel_svg(),'<b>Базовый сценарий к $1M (≈₽85 млн, 1700 оплат по 50К).</b> Строка ручного фулфилмента удалена, потолок исполнения снят.')}
  <div class="tw"><table><thead><tr><th>Параметр</th><th>Консерв.</th><th>Базовый</th><th>Агрессив.</th></tr></thead><tbody>
   <tr><td class="k">Рег → оплата (ставка) {GG}</td><td>3%</td><td>5%</td><td>8%</td></tr>
   <tr><td class="k">Оплат до $1M</td><td>1 700</td><td>1 700</td><td>1 700</td></tr>
   <tr><td class="k">Маркетинг, млн ₽</td><td>36.1</td><td>20.6</td><td>12.0</td></tr>
   <tr><td class="k">ДРР</td><td>42.5%</td><td>24.3%</td><td>14.1%</td></tr>
   <tr><td class="k">Валовая маржа</td><td>~89%</td><td>~89%</td><td>~89%</td></tr>
   <tr><td class="k">Чистая контрибуция, млн ₽</td><td>~39.5</td><td>~55.0</td><td>~63.6</td></tr>
  </tbody></table></div>
  {co('w','Ключ к прочтению',
     'Объёмный 50К даёт <strong>высокий ДРР</strong> (14–42%) — нужно 1700 единиц, значит много лидов. Раньше это '
     'убивало бы проект. Но при марже ~89% даже ДРР 24% оставляет <strong>~₽55 млн чистой контрибуции</strong>. '
     'Автоматизация не удешевила маркетинг — она сделала высокий ДРР <strong>терпимым</strong>. Плюс сверху — '
     'подписочный LTV. При провале конверсии до 1% (ДРР 72%) модель ломается → приоритет №0 — замер конверсии.')}
</section>""")

    B.append(f"""
<section class="sec"><div class="hd"><div class="n">Раздел 4</div><h2>Эксперименты, роадмап, запреты</h2></div>
  <h3>Топ-эксперименты (конверсия и доверие вперёд)</h3>
  <div class="tw"><table><thead><tr><th>ID</th><th>Гипотеза</th><th>Эффект</th></tr></thead><tbody>
   <tr><td class="k">E0</td><td>Микро-тест холодного трафика: замер рег→оплата + возвратов без человека</td><td>снимает риск ×10–60 млн ₽; валидирует модель и ставку доверия к ИИ</td></tr>
   <tr><td class="k">E-AI</td><td>A/B: чистая автоматика vs авто + опциональный живой звонок</td><td>теряет ли ИИ конверсию; калибрует custdev</td></tr>
   <tr><td class="k">E2</td><td>«Следующий шаг после отчёта» как апселл</td><td>прямой рост LTV</td></tr>
   <tr><td class="k">E-sub</td><td>Активация подписки после 50К</td><td>LTV сверх разовой выручки</td></tr>
  </tbody></table></div>
  {fig(roadmap_svg(),'<b>Пять горизонтов.</b> P0 «продуктизация проверки» снят (уже автоматизировано). Фокус — валидация спроса, затем масштаб.')}
  {co('r','Что НЕ делать (главный запрет развёрнут)',
     '<strong>Не масштабировать платный трафик до валидации конверсии и доверия к ИИ на холодном трафике.</strong> '
     'Раньше запрет был «не лить трафик до расшивки узкого места» — узкого места нет; теперь риск обратный: '
     'автоматика даёт ёмкость, но не гарантирует спрос. Также: не строить методологию-маркетплейс (IP), '
     'не конкурировать «тестом», не смешивать потоки, не откладывать подписку.')}
  {co('k','Итог для руководства',
     'Автоматизация сместила игру с производства на спрос — это лучше (спрос дешевле тестировать), но требует '
     'дисциплины: <strong>сначала доказать конверсию и доверие к ИИ, потом лить бюджет</strong>. Порядок: '
     'приборы → E0/E-AI → подписка → масштаб доказанного. Полный документ — <strong>docs/11-gtm-strategy.md</strong>.')}
</section>""")

    return "<!doctype html><html lang='ru'><head><meta charset='utf-8'><style>"+CSS+"</style></head><body>"+"".join(B)+"</body></html>"

def main():
    os.makedirs(OUT,exist_ok=True)
    doc=build()
    open(os.path.join(OUT,"gtm-exec-source.html"),"w",encoding="utf-8").write(doc)
    p=os.path.join(OUT,PDF)
    HTML(string=doc,base_url=OUT).write_pdf(p)
    print("PDF:",p,os.path.getsize(p),"bytes")

if __name__=="__main__":
    main()
