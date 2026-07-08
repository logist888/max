#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Executive summary GTM-стратегии MainExperts (docs/11-gtm-strategy.md).
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
  @bottom-left {{ content:"GTM-стратегия MainExperts · Executive Summary · путь к первому $1M";
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

def bottleneck_svg():
    s=['<svg viewBox="0 0 840 210" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    stages=[("Трафик Meta/ВК",P,190),("Скрининг",P,150),("Регистрация",IN,120),("Оплата 50К+",S,80)]
    x=15
    for lab,c,h in stages:
        y=(200-h)/2
        s.append(f'<rect x="{x}" y="{y:.0f}" width="120" height="{h}" rx="8" fill="#fff" stroke="{c}" stroke-width="2"/>')
        s.append(f'<text x="{x+60}" y="{100}" fill="{S}" font-size="10.5" font-weight="bold" text-anchor="middle">{lab}</text>')
        x+=155
    # bottleneck node (red, tiny)
    s.append(f'<rect x="{x}" y="78" width="130" height="44" rx="8" fill="#FEF2F2" stroke="{E}" stroke-width="2.4"/>')
    s.append(f'<text x="{x+65}" y="96" fill="{E}" font-size="10" font-weight="bold" text-anchor="middle">РУЧНАЯ ПРОВЕРКА</text>')
    s.append(f'<text x="{x+65}" y="111" fill="{E}" font-size="9" text-anchor="middle">9–10 в день · потолок</text>')
    for i in range(4):
        ax=15+i*155+120
        s.append(f'<path d="M{ax},100 H{ax+30}" stroke="{M}" stroke-width="2"/><path d="M{ax+30},95 l7,5 l-7,5 Z" fill="{M}"/>')
    s.append(f'<text x="420" y="150" fill="{E}" font-size="9.5" font-weight="bold" text-anchor="middle">1700 оплат × ручное касание = сервисная фирма, а не воронка → вся стратегия расшивает это горлышко</text>')
    s.append('</svg>');return "".join(s)

def funnel_svg():
    s=['<svg viewBox="0 0 840 200" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    steps=[("Бюджет","₽6.6 млн",P),("Лиды","25 952",P),("Регистрации",">40%",IN),("Оплаты","654",S),("Выручка","$1M",A)]
    W_,g=140,18;xs=[15+i*(W_+g) for i in range(5)];y=40;h=70
    for (t,v,c),x in zip(steps,xs):
        s.append(f'<rect x="{x}" y="{y}" width="{W_}" height="{h}" rx="10" fill="#fff" stroke="{c}" stroke-width="2"/>')
        s.append(f'<rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{c}"/>')
        s.append(f'<text x="{x+W_/2+3:.0f}" y="{y+30}" fill="{M}" font-size="9.5" text-anchor="middle">{t}</text>')
        s.append(f'<text x="{x+W_/2+3:.0f}" y="{y+52}" fill="{S}" font-size="14" font-weight="bold" text-anchor="middle">{v}</text>')
    for i in range(4):
        ax=xs[i]+W_;s.append(f'<path d="M{ax},{y+h/2:.0f} H{xs[i+1]-4}" stroke="{M}" stroke-width="2"/><path d="M{xs[i+1]-4},{y+h/2-5:.0f} l7,5 l-7,5 Z" fill="{M}"/>')
    s.append(f'<text x="420" y="150" fill="{M}" font-size="9.5" text-anchor="middle">Базовый сценарий: блендед-ACV ₽130К · конверсия рег→оплата 6% [ГИПОТЕЗА — центральная ставка] · ДРР 7.8%</text>')
    s.append(f'<text x="420" y="168" fill="{E}" font-size="9" text-anchor="middle">Реалистичный блендед ближе к консервативному (ACV×конверсия отрицательно коррелированы — см. аудит)</text>')
    s.append('</svg>');return "".join(s)

def roadmap_svg():
    s=['<svg viewBox="0 0 840 210" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    hs=[("30 дней","Приборы и ворота",P),("90 дней","Валидация ставки",IN),("6 мес","Повторяемая машина",A),("12 мес","Ров + Залив",CY),("24 мес","Актив данных",S)]
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
    s.append(f'<text x="420" y="150" fill="{M}" font-size="9.3" text-anchor="middle">Правило: сначала приборы и комплаенс-ворота → валидация центральной ставки на холодном трафике →</text>')
    s.append(f'<text x="420" y="166" fill="{M}" font-size="9.3" text-anchor="middle">масштаб ТОЛЬКО доказанного. Масштабировать до валидации гипотезы и расшивки горлышка — запрещено.</text>')
    s.append('</svg>');return "".join(s)

FF='<span class="tag t-f">ФАКТ</span>';OO='<span class="tag t-o">ОЦЕНКА</span>';GG='<span class="tag t-g">ГИПОТЕЗА</span>'

def build():
    B=[]
    B.append(f"""
<div class="cover"><div class="fr"></div><div class="wm">$1M</div>
  <div class="in"><div class="eb">MainExperts · docs/11</div><div class="kk">Executive Summary</div>
    <h1>GTM-стратегия:<br/>путь к первому<br/>миллиону долларов</h1>
    <div class="sub">Сжатие полной стратегии на 10 этапов, собранной независимым комитетом
      мирового уровня. Область — масштабируемая воронка (Поток-2). Каждый вывод помечен по
      достоверности; концепция проверена критически, а не подтверждена.</div></div>
  <div class="mt"><div>Внутренний документ · рабочий контекст, не выверенный источник</div>
    <div style="text-align:right">08.07.2026 · Конфиденциально</div></div></div>""")

    # 1. Мандат и главный вывод
    B.append(f"""
<section class="sec"><div class="hd"><div class="n">Раздел 1</div><h2>Мандат, рамка и главный вывод</h2></div>
  <div class="big">Самый вероятный путь к первому $1M — не в максимизации выручки, а в
    <strong>расшивке одного производственного горлышка</strong>. Пока каждую продажу тянет ручная
    экспертная проверка, Поток-2 ведёт себя как сервисная фирма, а не как воронка.</div>
  {co('i','Честная рамка (роль критика)',
     'Сырой $1M <strong>быстрее</strong> достигается через Поток-1 — личные HNW-продажи Макса '
     '(верхние тиры лесенки: Family Office ₽10M ≈ $117K, полная программа 7 мест ≈ ~$820K). '+FF+' '
     'Он сознательно <strong>вне анализа</strong>: это доход одного человека, а не масштабируемый '
     'актив. Поток-2 оптимизируется потому, что строит компанию, — и внутри него мы гонимся именно '
     'за скоростью к $1M.')}
  {fig(bottleneck_svg(),'<b>Узкое место.</b> ~1700 оплат пакета 50К для $1M при 9–10 ручных проверках в день. '
     'custdev требует эксперта (8/9) и видеозвонка до покупки (7/9) — на каждую сделку синхронное человеческое время.')}
  <h3>Три рычага обхода — и честный выбор</h3>
  <div class="tw"><table><thead><tr><th>Рычаг</th><th>Суть</th><th>Вердикт комитета</th></tr></thead><tbody>
   <tr><td class="k">A · Поднять ACV</td><td>пакет 150К, карта 500К → меньше единиц</td><td>быстрее к $1M, но дрейф к Поток-1 (см. оговорку)</td></tr>
   <tr><td class="k">B · Продуктизировать проверку</td><td>ИИ-черновик + тир человеческого касания</td><td class="k">сохраняет масштабируемость — приоритет №1</td></tr>
   <tr><td class="k">C · Сегмент высокого WTP</td><td>уйти в Залив/UAE</td><td>нет данных для отчёта + регуляторика детей</td></tr>
  </tbody></table></div>
  {co('w','Что комитет произносит прямо',
     'Масштабируемое ядро Поток-2 — это <strong>не отчёт за 50К</strong>, а бесплатный скрининг-крючок '
     '(лидоген) + подписка Pro/Ultima. Отчёт 50К — мост, а не двигатель. '+GG+' База ~50K юзеров '
     'при freemium 5–8% даёт ~2 500–4 000 платящих — на бумаге достижимо, если база активна.')}
</section>""")

    # 2. Рынки
    B.append(f"""
<section class="sec"><div class="hd"><div class="n">Раздел 2</div><h2>Рынки: рейтинг и роли</h2></div>
  <p class="lead">Логика выбора: первый рынок нужен там, где <strong>дешевле опровергнуть гипотезу</strong>
    скрининга, а не где выручка крупнее.</p>
  <div class="tw"><table><thead><tr><th>#</th><th>Рынок</th><th>Роль</th><th>Почему</th></tr></thead><tbody>
   <tr><td class="k">1</td><td class="k">Россия</td><td>Машина отладки и объёма</td><td>дешёвая итерация; hh.ru закрывает блокер данных {FF}; зрелый спрос; закрываемый юр-режим</td></tr>
   <tr><td class="k">2</td><td class="k">UAE / Залив</td><td>Премиум-пилот маржи ($)</td><td>экстремальный WTP (родители ~2× мирового среднего {OO}) обходит горлышко меньшим числом единиц; но Поток-2-трафик тут ещё ставка</td></tr>
   <tr><td class="k">3</td><td class="k">СНГ</td><td>Дешёвое расширение</td><td>переиспользование контента/платформы почти без затрат; ниже WTP</td></tr>
   <tr><td>4–5</td><td>Европа · США</td><td>Отложить</td><td>право на забвение конфликтует с «бессрочным профилем»; COPPA/FERPA/лицензии + дорогой трафик</td></tr>
   <tr><td>6–7</td><td>Азия · ЛатАм</td><td>Не сейчас</td><td>нет данных, fit и WTP-сигнала</td></tr>
  </tbody></table></div>
  {co('w','Конкурентная логика (Раздел 3, сжато)',
     'Тест-профориентация коммодитизирован: ₽349–7 000 или <strong>бесплатно</strong> (MAXIMUM, Foxford — как лидоген). '
     +OO+' Побеждать «тестом» = гонка ко дну. Свободная ниша — <strong>премиальное лонгитюдное сопровождение</strong> '
     'будущего ребёнка + закрытие разрыва «нет следующего шага после отчёта».')}
</section>""")

    # 3. Выбор стратегии
    B.append(f"""
<section class="sec"><div class="hd"><div class="n">Раздел 4</div><h2>Выбор стратегии: основной и резервный</h2></div>
  <p class="lead">Из 5 сценариев судейская панель (impact / скорость / вероятность / цена / масштаб / риск)
    вывела двух лидеров.</p>
  <div class="tw"><table><thead><tr><th>Сценарий</th><th>Тезис</th><th>Оценка</th><th>Роль</th></tr></thead><tbody>
   <tr><td class="k">S2 · Консультационный контур 150К+</td><td>отчёт — лид-магнит; ACV 150К+ сокращает единицы ~1700 → ~570, ручная проверка вмещается в мощность и тарифицируется</td><td class="k">21.0</td><td class="k">ОСНОВНОЙ</td></tr>
   <tr><td class="k">S5 · SEO-агрегатор «Топ профориентации РФ»</td><td>freemium + органика как CAC-редуктор</td><td>19.0</td><td>наслаивать</td></tr>
   <tr><td class="k">S1 · РФ-PLG на данных hh.ru</td><td>чистый Поток-2: скрининг → Профиль 360 (50К) → подписка Pro/Ultima</td><td>18.7</td><td class="k">РЕЗЕРВНЫЙ</td></tr>
   <tr><td>S3 · Премиум Залива</td><td>опцион на экстремальном WTP</td><td>14.7</td><td>гейтится</td></tr>
   <tr><td>S4 · Marketplace экспертов</td><td>распределить горлышко сетью</td><td>12.0</td><td>припаркован (IP)</td></tr>
  </tbody></table></div>
  {co('i','⚠️ Оговорка о границе потоков (важно для основателя)',
     'S2 использует ценовую точку 150К, которую канон относит к <strong>Поток-1</strong>. Разрешение: границу '
     'проводим по <strong>каналу и поставке</strong> — S2 = воронкой-привлечённый, экспертной сетью исполненный '
     'SKU (не личные продажи Макса). '
     'Если вы считаете ₽150К+ по определению Поток-1 — основным становится <strong>резервный S1</strong> '
     '(чистая воронка 50К + подписка). Выбор primary↔backup — ваше решение о границе; оба просчитаны.')}
</section>""")

    # 4. Финмодель
    B.append(f"""
<section class="sec"><div class="hd"><div class="n">Раздел 5</div><h2>Финансовая модель: воронка до $1M</h2></div>
  {fig(funnel_svg(),'<b>Базовый сценарий к $1M (≈₽85 млн).</b> Три варианта дают 944 / 654 / 425 единиц (консерв./база/агрессив).')}
  <div class="tw"><table><thead><tr><th>Параметр</th><th>Консерв.</th><th>Базовый</th><th>Агрессив.</th></tr></thead><tbody>
   <tr><td class="k">Рег → оплата (ставка) {GG}</td><td>4%</td><td>6%</td><td>8%</td></tr>
   <tr><td class="k">Блендед ACV, ₽</td><td>90 000</td><td>130 000</td><td>200 000</td></tr>
   <tr><td class="k">Единиц до $1M</td><td>944</td><td>654</td><td>425</td></tr>
   <tr><td class="k">Маркетинг, млн ₽</td><td>15.0</td><td>6.6</td><td>3.0</td></tr>
   <tr><td class="k">ДРР</td><td>17.7%</td><td>7.8%</td><td>3.5%</td></tr>
   <tr><td class="k">В день (130 раб. дней)</td><td>~7.3</td><td>~5.0</td><td>~3.3</td></tr>
  </tbody></table></div>
  {co('r','Центральная ставка и аудиторская правка',
     'Всё держится на конверсии рег→оплата. При 1% нужно 155 714 лидов и ДРР 46.7% — модель ломается. '
     '<strong>Приоритет №1 — замерить блендед-конверсию на 3–5 тыс. регистраций ДО масштабирования.</strong> '
     'Аудит: столбцы «база/агрессив» оптимистичны сразу по двум осям (высокий ACV И высокая конверсия '
     'отрицательно коррелированы) — читать как верхнюю границу; реалистичный блендед ближе к консервативу.')}
</section>""")

    # 5. Эксперименты
    B.append(f"""
<section class="sec"><div class="hd"><div class="n">Раздел 6</div><h2>Топ-эксперименты (по приоритету)</h2></div>
  <p class="lead">Backlog из 15 гипотез; ниже — верх по системе оценки (влияние на $1M × скорость, инверсия
    стоимости/сложности/риска).</p>
  <div class="tw"><table><thead><tr><th>ID</th><th>Гипотеза</th><th>Ожидаемый эффект</th></tr></thead><tbody>
   <tr><td class="k">E-fin</td><td>Замер блендед-конверсии на 3–5К регистраций до масштаба</td><td>снимает риск ×10–40 млн ₽; валидирует/убивает модель</td></tr>
   <tr><td class="k">E2</td><td>«Следующий шаг после отчёта» — план действий как платный апселл</td><td>закрывает главный инсайт custdev; прямой рост LTV</td></tr>
   <tr><td class="k">E3</td><td>ACV-тест: 50К vs 150К (с консультацией) как якорь</td><td>втрое меньше единиц на тот же $ → обход горлышка</td></tr>
   <tr><td class="k">E1</td><td>Продуктизация отчёта: ИИ-черновик + ревью 15 мин + тир касания</td><td>пропускная способность с 5/очередь до ~9+</td></tr>
   <tr><td class="k">E5</td><td>Реферал родитель→родитель (доверие через рекомендации {FF})</td><td>снижение CAC</td></tr>
   <tr><td class="k">E8</td><td>Ценовое якорение 50→150→500К (decoy) vs одиночный 50К</td><td>+10–20% средний чек без роста трафика</td></tr>
  </tbody></table></div>
</section>""")

    # 6. Роадмап + что не делать
    B.append(f"""
<section class="sec"><div class="hd"><div class="n">Раздел 7</div><h2>План реализации и запреты</h2></div>
  {fig(roadmap_svg(),'<b>Пять горизонтов.</b> Вебинар (был предв. 4 июля) — исход [НЕИЗВЕСТНО]: план ветвится на «состоялся» / «перенесён».')}
  <h3>30 дней — «Приборы и ворота» (P0)</h3>
  <ul>
   <li><strong>Комплаенс-гейт:</strong> согласия на данные детей 10–18, хранение, дисклеймер, переименование тестов в клиентских частях — до трафика.</li>
   <li><strong>Сквозная аналитика воронки</strong> роль→квиз→email→риск-профиль→3 CTA (без неё все KPI — фантомы).</li>
   <li><strong>Закрыть «нет следующего шага»</strong> после отчёта — прямой рычаг LTV.</li>
   <li>Микро-тест трафика $1500–2000; <strong>ручную доставку НЕ чинить — только замерить</strong> (горлышко пока не активно).</li>
  </ul>
  <h3>90 дней — «Валидация ставки»</h3>
  <ul>
   <li><strong>Проверить гипотезу скрининга холодным трафиком</strong> {GG} (тёплый контакт смещён) — платит ли холодный родитель.</li>
   <li>Продуктизация ревью, пока объём мал и ошибка дешева; достроить методологию скрининга (блокер).</li>
   <li>Подписку: отгрузить крючок накопления профиля, полный биллинг — с критического пути.</li>
  </ul>
  {co('r','Что НЕ делать',
     '<strong>Не масштабировать трафик</strong> до валидации центральной ставки и расшивки горлышка (сжечь бюджет на нерабочей экономике). '
     '<strong>Не строить</strong> методологию-маркетплейс (IP заблокирован). <strong>Не конкурировать «тестом»</strong> (race-to-free). '
     '<strong>Не смешивать потоки.</strong> Осторожно с психодиагностикой на детях (граница регулируется).')}
  {co('k','Итог для руководства',
     'Не гнаться за выручкой на непроверенной модели. Порядок: приборы → валидация ставки на холодном трафике → '
     'расшивка горлышка (ACV + продуктизация) → масштаб <strong>только доказанного</strong>. Полный документ с '
     '10 этапами, финмоделью и приоритизированным backlog — <strong>docs/11-gtm-strategy.md</strong>.')}
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
