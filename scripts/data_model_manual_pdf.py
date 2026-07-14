#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширенный мануал по модели данных docs/10-data-model.md.
Объясняет ВЗАИМОСВЯЗИ и ПОЧЕМУ они устроены так. Дизайн-грейд:
A4, поля 20 мм, DejaVu Sans, палитра бренда, рисованные схемы паттернов,
таблицы обоснований, разбор анти-паттернов. Рендер: WeasyPrint.
Выход: Модель_данных_расширенный_мануал.pdf
"""
import os
from weasyprint import HTML

OUT_DIR=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","vault","40-reports","playbook-otzyvy"))
PDF_NAME="Модель_данных_расширенный_мануал.pdf"

PRIMARY="#1D4ED8";SECONDARY="#0F172A";ACCENT="#10B981";WARNING="#F59E0B"
ERROR="#DC2626";INDIGO="#4338CA";CYAN="#0891B2";INK="#1E293B";MUTED="#64748B"
LINE="#E2E8F0";BG="#F8FAFC"

CSS=f"""
@page {{ size:A4; margin:20mm 20mm 18mm 20mm;
  @bottom-left {{ content:"Мануал · Модель данных MainExperts · взаимосвязи и их логика";
    font-family:'DejaVu Sans';font-size:7.5pt;color:{MUTED}; }}
  @bottom-right {{ content:counter(page);font-family:'DejaVu Sans';font-size:8.5pt;font-weight:bold;color:{SECONDARY}; }}
  @top-right {{ content:string(chap);font-family:'DejaVu Sans';font-size:7.5pt;color:{MUTED}; }}
}}
@page cover {{ margin:0; @bottom-left{{content:none}} @bottom-right{{content:none}} @top-right{{content:none}} }}
*{{box-sizing:border-box}}
html{{font-family:'DejaVu Sans',sans-serif}}
body{{margin:0;color:{INK};font-size:11pt;line-height:1.44}}
p{{margin:0 0 7pt 0;text-align:justify}}
strong{{color:{SECONDARY}}}
h1,h2,h3{{margin:0;color:{SECONDARY};line-height:1.15}}
ul{{margin:0 0 8pt 0;padding-left:15pt}} li{{margin:0 0 4pt 0}}
.small{{font-size:9pt;color:{MUTED}}}

.cover{{page:cover;height:297mm;position:relative;color:#fff;
  background:radial-gradient(1100px 480px at 78% -10%,rgba(29,78,216,.4),transparent 60%),
  linear-gradient(155deg,{SECONDARY} 0%,#152a5e 50%,{INDIGO} 100%);overflow:hidden}}
.cover .frame{{position:absolute;inset:14mm;border:1px solid rgba(255,255,255,.22)}}
.cover .in{{position:absolute;inset:32mm 32mm}}
.cover .eyebrow{{letter-spacing:.4em;font-size:11pt;text-transform:uppercase;color:rgba(255,255,255,.72);margin-bottom:8mm}}
.cover .kick{{display:inline-block;font-size:9.5pt;letter-spacing:.26em;text-transform:uppercase;
  color:{ACCENT};border:1px solid rgba(16,185,129,.5);padding:3pt 10pt;border-radius:20pt;margin-bottom:12mm}}
.cover h1{{color:#fff;font-size:36pt;line-height:1.1;margin:0 0 6mm;letter-spacing:-.5pt}}
.cover .sub{{font-size:13.5pt;color:rgba(255,255,255,.86);max-width:150mm;line-height:1.5}}
.cover .meta{{position:absolute;left:32mm;right:32mm;bottom:24mm;font-size:8.5pt;color:rgba(255,255,255,.6);
  border-top:1px solid rgba(255,255,255,.2);padding-top:5mm;display:flex;justify-content:space-between}}
.cover .wm{{position:absolute;right:-24mm;top:150mm;font-size:150pt;font-weight:bold;color:rgba(255,255,255,.05)}}

/* оглавление */
.toc{{border:1px solid {LINE};border-radius:10pt;overflow:hidden;margin-top:8pt}}
.toc .r{{display:table;width:100%;border-top:1px solid {LINE}}} .toc .r:first-child{{border-top:none}}
.toc .n{{display:table-cell;width:34pt;background:{BG};text-align:center;font-weight:bold;color:{PRIMARY};vertical-align:middle;padding:7pt}}
.toc .t{{display:table-cell;padding:7pt 11pt;font-size:10.5pt;vertical-align:middle}} .toc .t b{{color:{SECONDARY}}}

/* глава */
.chap{{break-before:page}}
.chaphdr{{background:linear-gradient(120deg,{SECONDARY},{INDIGO});color:#fff;border-radius:12pt;
  padding:16pt 18pt;margin-bottom:14pt}}
.chaphdr .no{{font-size:9.5pt;letter-spacing:.28em;text-transform:uppercase;color:rgba(255,255,255,.7)}}
.chaphdr h2{{color:#fff;font-size:21pt;margin:4pt 0 5pt;line-height:1.14}}
.chaphdr .lead{{font-size:11pt;color:rgba(255,255,255,.86);max-width:150mm}}
h3{{font-size:14pt;color:{PRIMARY};margin:12pt 0 5pt}}
.eyebrow{{font-size:8.5pt;letter-spacing:.2em;text-transform:uppercase;font-weight:bold;color:{PRIMARY};margin:10pt 0 4pt}}

figure{{margin:10pt 0;break-inside:avoid}}
.schema{{border:1px solid {LINE};border-radius:10pt;background:#fff;padding:12pt}}
.schema svg{{width:100%;height:auto;display:block}}
figcaption{{font-size:8.7pt;color:{MUTED};margin-top:7pt;padding-top:6pt;border-top:1px dashed {LINE}}}
figcaption b{{color:{PRIMARY}}}

.tw{{border:1px solid {LINE};border-radius:9pt;overflow:hidden;margin:10pt 0;break-inside:avoid}}
table{{border-collapse:collapse;width:100%;font-size:9.6pt}}
thead th{{background:{PRIMARY};color:#fff;text-align:left;padding:7pt 9pt;font-size:9pt;border-right:1px solid rgba(255,255,255,.15)}}
thead th:last-child{{border-right:none}}
td{{padding:6.5pt 9pt;border-top:1px solid {LINE};vertical-align:top;line-height:1.36}}
tbody tr:nth-child(even){{background:{BG}}}
td.k{{font-weight:bold;color:{SECONDARY}}}
table.why thead th{{background:{SECONDARY}}}
table.anti thead th{{background:{ERROR}}}

.callout{{display:table;width:100%;border-radius:8pt;padding:10pt 12pt;margin:10pt 0;border:1px solid;break-inside:avoid}}
.callout .bd{{display:table-cell;font-size:10pt;line-height:1.44}}
.callout .h{{font-weight:bold;font-size:10.5pt;margin-bottom:2pt}}
.c-why{{background:#EFF4FF;border-color:{PRIMARY}}} .c-why .h{{color:{PRIMARY}}}
.c-imp{{background:#FFFBEB;border-color:{WARNING}}} .c-imp .h{{color:#92400E}}
.c-key{{background:#ECFDF5;border-color:{ACCENT}}} .c-key .h{{color:#065F46}}
.c-anti{{background:#FEF2F2;border-color:{ERROR}}} .c-anti .h{{color:{ERROR}}}

.lead-in{{color:{MUTED};font-size:11pt;line-height:1.5;margin-bottom:8pt}}
.divider{{display:flex;align-items:center;gap:9pt;margin:14pt 0;color:{LINE}}}
.divider::before,.divider::after{{content:"";flex:1;height:1px;background:{LINE}}}
.divider .d{{width:7pt;height:7pt;background:{ACCENT};transform:rotate(45deg)}}
"""

# ─────────────────────────── СХЕМЫ ───────────────────────────
def spine():
    nodes=[("Product",PRIMARY,"концепт"),("SKU",PRIMARY,"вариант"),("Listing",INDIGO,"размещение"),
           ("Market × Channel",SECONDARY,"контекст"),("Fact",ACCENT,"событие")]
    W,gap=150,26;xs=[15+i*(W+gap) for i in range(5)];y=20;h=54
    s=[f'<svg viewBox="0 0 {xs[-1]+W+15} 120" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    for x,(lab,c,sub) in zip(xs,nodes):
        s.append(f'<rect x="{x}" y="{y}" width="{W}" height="{h}" rx="11" fill="#fff" stroke="{c}" stroke-width="2"/>')
        s.append(f'<rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{c}"/>')
        s.append(f'<text x="{x+W/2+3:.0f}" y="{y+24}" fill="{SECONDARY}" font-size="13" font-weight="bold" text-anchor="middle">{lab}</text>')
        s.append(f'<text x="{x+W/2+3:.0f}" y="{y+41}" fill="{MUTED}" font-size="10" text-anchor="middle">{sub}</text>')
    for i in range(4):
        ax=xs[i]+W;s.append(f'<path d="M{ax},{y+h/2:.0f} H{xs[i+1]-4}" stroke="{MUTED}" stroke-width="2"/>')
        s.append(f'<path d="M{xs[i+1]-4},{y+h/2-5:.0f} l7,5 l-7,5 Z" fill="{MUTED}"/>')
    s.append(f'<text x="{xs[0]+W/2:.0f}" y="95" fill="{MUTED}" font-size="10" text-anchor="middle">не знает о ценах</text>')
    s.append(f'<text x="{xs[2]+W/2:.0f}" y="95" fill="{MUTED}" font-size="10" text-anchor="middle">знает цену и язык</text>')
    s.append(f'<text x="{xs[4]+W/2:.0f}" y="95" fill="{MUTED}" font-size="10" text-anchor="middle">ссылается на листинг</text>')
    s.append('</svg>');return "".join(s)

def cardinality():
    s=['<svg viewBox="0 0 840 250" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    def box(x,y,w,h,c,t1,t2=""):
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#fff" stroke="{c}" stroke-width="2"/>')
        s.append(f'<text x="{x+w/2:.0f}" y="{y+(h/2+5 if not t2 else h/2-2):.0f}" fill="{SECONDARY}" font-size="12.5" font-weight="bold" text-anchor="middle">{t1}</text>')
        if t2:s.append(f'<text x="{x+w/2:.0f}" y="{y+h/2+14:.0f}" fill="{MUTED}" font-size="10" text-anchor="middle">{t2}</text>')
    def arr(x1,y1,x2,y2,lab):
        s.append(f'<path d="M{x1},{y1} H{x2-4}" stroke="{MUTED}" stroke-width="2"/>')
        s.append(f'<path d="M{x2-4},{y1-5} l7,5 l-7,5 Z" fill="{MUTED}"/>')
        s.append(f'<text x="{(x1+x2)/2:.0f}" y="{y1-8}" fill="{PRIMARY}" font-size="11" font-weight="bold" text-anchor="middle">{lab}</text>')
    box(15,95,150,52,PRIMARY,"products");box(235,95,150,52,PRIMARY,"skus");box(455,95,160,52,INDIGO,"listings")
    arr(165,121,235,121,"1 : ∞");arr(385,121,455,121,"1 : ∞")
    box(675,20,150,50,SECONDARY,"markets");box(675,172,150,50,SECONDARY,"channels")
    s.append(f'<path d="M750,70 C750,100 640,110 619,118" stroke="{MUTED}" stroke-width="2" fill="none"/>')
    s.append(f'<path d="M623,114 l-8,4 l3,-8 Z" fill="{MUTED}"/>')
    s.append(f'<path d="M750,172 C750,142 640,132 619,124" stroke="{MUTED}" stroke-width="2" fill="none"/>')
    s.append(f'<path d="M623,128 l-8,-4 l3,8 Z" fill="{MUTED}"/>')
    s.append(f'<text x="700" y="100" fill="{PRIMARY}" font-size="11" font-weight="bold">∞ : 1</text>')
    s.append(f'<text x="700" y="160" fill="{PRIMARY}" font-size="11" font-weight="bold">∞ : 1</text>')
    s.append(f'<text x="535" y="185" fill="{MUTED}" font-size="10.5" text-anchor="middle">тройка (SKU · Channel · Market) — уникальна</text>')
    s.append('</svg>');return "".join(s)

def price_timeline():
    s=['<svg viewBox="0 0 840 200" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    x0,x1=40,800;y=120;mid=x0+(x1-x0)*14/30
    s.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{LINE}" stroke-width="2"/>')
    for d in [1,10,14,16,30]:
        px=x0+(x1-x0)*(d-1)/29
        s.append(f'<line x1="{px:.0f}" y1="{y-4}" x2="{px:.0f}" y2="{y+4}" stroke="{MUTED}" stroke-width="1.5"/>')
        s.append(f'<text x="{px:.0f}" y="{y+18}" fill="{MUTED}" font-size="9.5" text-anchor="middle">июн {d}</text>')
    s.append(f'<rect x="{x0}" y="{y-40}" width="{mid-x0:.0f}" height="26" rx="6" fill="#EFF4FF" stroke="{PRIMARY}" stroke-width="1.5"/>')
    s.append(f'<text x="{(x0+mid)/2:.0f}" y="{y-22}" fill="{PRIMARY}" font-size="11" font-weight="bold" text-anchor="middle">PP_MUG_AMZ_1 · $24.90</text>')
    s.append(f'<rect x="{mid:.0f}" y="{y-40}" width="{x1-mid:.0f}" height="26" rx="6" fill="#ECFDF5" stroke="{ACCENT}" stroke-width="1.5"/>')
    s.append(f'<text x="{(mid+x1)/2:.0f}" y="{y-22}" fill="#065F46" font-size="11" font-weight="bold" text-anchor="middle">PP_MUG_AMZ_2 · $27.90</text>')
    for d,lab,c in [(10,"ORD001",PRIMARY),(16,"ORD004",ACCENT)]:
        px=x0+(x1-x0)*(d-1)/29
        s.append(f'<circle cx="{px:.0f}" cy="{y}" r="5" fill="{c}"/>')
        s.append(f'<path d="M{px:.0f},{y+30} V{y+6}" stroke="{c}" stroke-width="1.6" stroke-dasharray="3 3"/>')
        s.append(f'<text x="{px:.0f}" y="{y+45}" fill="{c}" font-size="10.5" font-weight="bold" text-anchor="middle">{lab}</text>')
    s.append(f'<text x="{mid:.0f}" y="{y-48}" fill="{ERROR}" font-size="9.5" text-anchor="middle">смена цены</text>')
    s.append('</svg>');return "".join(s)

def goals_tree():
    s=['<svg viewBox="0 0 840 300" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    def box(x,y,w,h,c,t,sub=""):
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="#fff" stroke="{c}" stroke-width="2"/>')
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="5" rx="2.5" fill="{c}"/>')
        s.append(f'<text x="{x+w/2:.0f}" y="{y+(h/2+8 if not sub else h/2+2):.0f}" fill="{SECONDARY}" font-size="11.5" font-weight="bold" text-anchor="middle">{t}</text>')
        if sub:s.append(f'<text x="{x+w/2:.0f}" y="{y+h/2+16:.0f}" fill="{MUTED}" font-size="9" text-anchor="middle">{sub}</text>')
    box(330,10,180,40,SECONDARY,"Business Objective")
    box(330,72,180,40,PRIMARY,"Marketing Objective")
    s.append(f'<path d="M420,50 V72" stroke="{MUTED}" stroke-width="2"/>')
    ch=[(30,PRIMARY,"Campaign","восприятие · поведение"),(310,WARNING,"Channel","эффективность · цикл"),(590,ERROR,"Test","обучение · решение")]
    for x,c,t,sub in ch:
        box(x,160,220,50,c,t+" Objective",sub)
        s.append(f'<path d="M420,112 V135 H{x+110} V160" stroke="{MUTED}" stroke-width="1.6" fill="none"/>')
    # kpi + outcomes
    box(30,250,220,38,INDIGO,"kpi_definitions","формула из фактов")
    box(590,250,220,38,ACCENT,"outcomes","факт vs target")
    s.append(f'<path d="M140,210 V250" stroke="{INDIGO}" stroke-width="1.4" stroke-dasharray="3 3"/>')
    s.append(f'<path d="M700,210 V250" stroke="{ACCENT}" stroke-width="1.4" stroke-dasharray="3 3"/>')
    s.append('</svg>');return "".join(s)

def flow():
    s=['<svg viewBox="0 0 840 150" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    nodes=[("Событие",MUTED),("Факт",ACCENT),("Каталог KPI",PRIMARY),("Витрина",INDIGO),("Решение",SECONDARY),("Знание",ACCENT)]
    W,gap=118,15;xs=[12+i*(W+gap) for i in range(6)];y=45;h=50
    for x,(lab,c) in zip(xs,nodes):
        s.append(f'<rect x="{x}" y="{y}" width="{W}" height="{h}" rx="10" fill="#fff" stroke="{c}" stroke-width="2"/>')
        s.append(f'<text x="{x+W/2:.0f}" y="{y+h/2+5:.0f}" fill="{SECONDARY}" font-size="11.5" font-weight="bold" text-anchor="middle">{lab}</text>')
    for i in range(5):
        ax=xs[i]+W;s.append(f'<path d="M{ax},{y+h/2:.0f} H{xs[i+1]-4}" stroke="{MUTED}" stroke-width="2"/>')
        s.append(f'<path d="M{xs[i+1]-4},{y+h/2-5:.0f} l7,5 l-7,5 Z" fill="{MUTED}"/>')
    s.append(f'<text x="{xs[1]+W/2:.0f}" y="{y-6}" fill="{MUTED}" font-size="9" text-anchor="middle">append-only</text>')
    s.append(f'<text x="{xs[2]+W/2:.0f}" y="{y-6}" fill="{MUTED}" font-size="9" text-anchor="middle">SSOT · формулы</text>')
    s.append(f'<text x="{xs[4]+W/2:.0f}" y="{y-6}" fill="{MUTED}" font-size="9" text-anchor="middle">всегда человек</text>')
    # loop back knowledge->decision area
    s.append(f'<path d="M{xs[5]+W/2:.0f},{y+h} V{y+h+18} H{xs[2]+W/2:.0f} V{y+h}" stroke="{ACCENT}" stroke-width="1.5" fill="none" stroke-dasharray="5 4"/>')
    s.append(f'<path d="M{xs[2]+W/2-5:.0f},{y+h+4} l5,-6 l5,6 Z" fill="{ACCENT}"/>')
    s.append(f'<text x="{(xs[2]+xs[5])/2+W/2:.0f}" y="{y+h+30}" fill="#065F46" font-size="9" text-anchor="middle">знание улучшает каталог и playbook</text>')
    s.append('</svg>');return "".join(s)

def inventory():
    s=['<svg viewBox="0 0 840 220" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    s.append(f'<rect x="330" y="12" width="180" height="44" rx="10" fill="#fff" stroke="{PRIMARY}" stroke-width="2"/>')
    s.append(f'<text x="420" y="32" fill="{SECONDARY}" font-size="12" font-weight="bold" text-anchor="middle">SKU_MUG_BLACK_500</text>')
    s.append(f'<text x="420" y="47" fill="{MUTED}" font-size="9.5" text-anchor="middle">один вариант</text>')
    # warehouses (сток)
    for x,lab,q in [(230,"WH_US_EAST","120 шт"),(430,"WH_DE_CENTRAL","60 шт")]:
        s.append(f'<rect x="{x}" y="86" width="180" height="44" rx="10" fill="#ECFDF5" stroke="{ACCENT}" stroke-width="1.8"/>')
        s.append(f'<text x="{x+90}" y="106" fill="#065F46" font-size="11" font-weight="bold" text-anchor="middle">{lab}</text>')
        s.append(f'<text x="{x+90}" y="121" fill="#065F46" font-size="10" text-anchor="middle">остаток: {q}</text>')
        s.append(f'<path d="M420,56 C420,70 {x+90},72 {x+90},86" stroke="{ACCENT}" stroke-width="1.8" fill="none"/>')
    s.append(f'<text x="640" y="112" fill="#065F46" font-size="10.5" font-weight="bold">сток живёт здесь</text>')
    # listings (делят сток)
    for x,lab in [(40,"LST_AMZ_US_MUG"),(240,"LST_WEB_US_MUG"),(440,"LST_WEB_DE_MUG"),(640,"LST_WEB_RU_MUG")]:
        s.append(f'<rect x="{x}" y="165" width="160" height="34" rx="8" fill="{BG}" stroke="{LINE}" stroke-width="1.2"/>')
        s.append(f'<text x="{x+80}" y="186" fill="{INK}" font-size="9.8" text-anchor="middle">{lab}</text>')
        s.append(f'<path d="M420,56 C420,120 {x+80},130 {x+80},165" stroke="{MUTED}" stroke-width="1.2" fill="none" stroke-dasharray="3 3"/>')
    s.append(f'<text x="420" y="215" fill="{ERROR}" font-size="10" font-weight="bold" text-anchor="middle">4 листинга делят один сток — привяжи остаток к листингу, и запас задвоится</text>')
    s.append('</svg>');return "".join(s)

# ─────────────────────────── ХЕЛПЕРЫ ───────────────────────────
def fig(svg,cap):return f'<figure><div class="schema">{svg}<figcaption>{cap}</figcaption></div></figure>'
def callout(kind,h,b):return f'<div class="callout c-{kind}"><div class="bd"><div class="h">{h}</div>{b}</div></div>'
def wtable(headers,rows,cls="why"):
    th="".join(f"<th>{x}</th>" for x in headers)
    def cell(i,c):
        kcls=' class="k"' if i==0 else ''
        return f'<td{kcls}>{c}</td>'
    body="".join("<tr>"+"".join(cell(i,c) for i,c in enumerate(r))+"</tr>" for r in rows)
    return f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'
def chap(no,title,lead,body):
    return (f'<section class="chap"><div class="chaphdr" style="string-set:chap \'{title}\'">'
            f'<div class="no">Глава {no}</div><h2>{title}</h2><div class="lead">{lead}</div></div>{body}</section>')

# ─────────────────────────── КОНТЕНТ ───────────────────────────
def build():
    B=[]
    B.append(f"""
<div class="cover"><div class="frame"></div><div class="wm">10</div>
  <div class="in"><div class="eyebrow">MainExperts · docs/10</div>
    <div class="kick">Расширенный мануал</div>
    <h1>Модель данных:<br/>взаимосвязи<br/>и их логика</h1>
    <div class="sub">Не «что это за таблица», а <b style="color:#fff">почему связи устроены именно так</b>.
      Каждое решение модели — направление ссылки, кратность, датированность, отделение плана от факта —
      разобрано с обоснованием и с разбором «почему не иначе».</div>
  </div>
  <div class="meta"><div>Внутренний документ · рабочий контекст, не выверенный источник</div>
    <div style="text-align:right">08.07.2026 · Конфиденциально</div></div></div>""")

    # оглавление / как читать
    toc=[("Как читать этот мануал","от ядра к правилам, каждый раздел отвечает «почему»"),
         ("Ядро онтологии: шесть уровней","почему концепт, вариант и размещение разделены"),
         ("Связи ядра: направление и кратность","почему дети ссылаются на родителя, а факт — на листинг"),
         ("Время в модели: почему всё датировано","цена, курс, налог и себестоимость «на дату факта»"),
         ("Единый дом факта: без дублирования","у каждого факта ровно одно место жизни"),
         ("Слой целей: план отделён от факта","почему три типа целей и почему outcomes ≠ target"),
         ("Фактовый слой: append-only","почему факты не редактируются, а исправляются строкой"),
         ("От события к решению","почему витрины считают, а не хранят"),
         ("Почему НЕ иначе: анти-паттерны","соблазн → почему ломается → что делаем"),
         ("Приложение: шесть паттернов связей","вся модель сводится к шести формам отношений")]
    B.append('<section class="chap"><div class="eyebrow">Оглавление</div>'
             '<h2 style="font-size:20pt;border-bottom:2.5pt solid '+PRIMARY+';padding-bottom:5pt">Как читать этот мануал</h2>')
    B.append('<p class="lead-in">Мануал объясняет <strong>взаимосвязи</strong> модели данных и их логику. '
             'Порядок — от ядра к правилам: сначала из чего собрана онтология, затем как связаны сущности, '
             'потом сквозные принципы (время, единый дом факта, план/факт), и наконец — почему альтернативы хуже. '
             'Каждый раздел отвечает на один вопрос: <strong>почему именно так</strong>.</p>')
    rows="".join(f'<div class="r"><div class="n">{i}</div><div class="t"><b>{t}</b> — {d}</div></div>'
                 for i,(t,d) in enumerate(toc,0) if i>0)
    # первый пункт «как читать» — это текущая страница, нумеруем главы 1..9 + приложение
    rows=""
    labels=[("1","Ядро онтологии: шесть уровней"),("2","Связи ядра: направление и кратность"),
            ("3","Время в модели: почему всё датировано"),("4","Единый дом факта: без дублирования"),
            ("5","Слой целей: план отделён от факта"),("6","Фактовый слой: append-only"),
            ("7","От события к решению"),("8","Почему НЕ иначе: анти-паттерны"),("A","Приложение: шесть паттернов связей")]
    descs=["почему концепт, вариант и размещение разделены","почему дети ссылаются на родителя, а факт — на листинг",
           "цена, курс, налог, себестоимость — «на дату факта»","у каждого факта ровно одно место жизни",
           "почему три типа целей и почему outcomes ≠ target","почему факты исправляются строкой, а не правкой",
           "почему витрины считают, а не хранят","соблазн → почему ломается → что делаем",
           "вся модель сводится к шести формам отношений"]
    rows="".join(f'<div class="r"><div class="n">{n}</div><div class="t"><b>{t}</b> — {d}</div></div>'
                 for (n,t),d in zip(labels,descs))
    B.append(f'<div class="toc">{rows}</div>')
    B.append(callout("key","Один принцип над всеми",
        "Модель хранит <b>истину как она была в момент события</b> и никогда не смешивает <b>факт</b> "
        "(что случилось) с <b>планом</b> (что хотели) и <b>справочником</b> (как устроен мир). "
        "Все частные правила ниже — следствия этого одного."))
    B.append('</section>')

    # Глава 1
    b=f"""
    <p class="lead-in">Ядро — шесть уровней. Их нельзя схлопнуть в одну сущность, потому что они отвечают
    на разные вопросы: <strong>что это</strong>, <strong>какой именно</strong>, <strong>где и как продаётся</strong>,
    <strong>в каком контексте</strong> и <strong>что произошло</strong>.</p>
    {fig(spine(),"<b>Схема 1.</b> Ядро онтологии. Слева направо растёт конкретность: концепт → вариант → размещение → контекст → событие. Знание о цене и языке появляется только на листинге — не раньше.")}
    <h3>Почему концепт, вариант и размещение — разные сущности</h3>
    <p>Соблазн — держать «товар» одной строкой с ценой и названием. Он ломается на второй стране: у одного
    товара оказывается много цен, языков и каналов. Разделение снимает это раз и навсегда:</p>
    {wtable(["Уровень","Что это","Что НЕ хранит","Почему"],[
     ["products","Глобальный концепт («что это по сути»)","цену, язык, канал","чтобы один продукт жил на N рынках без копий"],
     ["skus","Конкретный вариант/оффер","цену, размещение","варианты (цвет, объём, тариф) отличаются, но это тот же продукт"],
     ["listings","Продаваемое размещение = SKU × канал × рынок","историю продаж","единица, к которой привязаны цена, контент, факты"],
     ["markets / channels","Контекст: страна/валюта/налог и площадка","товар","один контекст переиспользуется всеми листингами"],
     ["Fact","Событие или измерение","справочные атрибуты","хранит, что случилось, ссылаясь на листинг"],
    ])}
    {callout("why","Почему продукт не знает о цене","Цена — свойство <b>сделки в контексте</b> (рынок, канал, момент), а не свойство вещи. "
     "Положи цену на продукт — и придётся дублировать продукт под каждую страну и каждую акцию. Продукт — существительное («что есть»), листинг — глагол («как продаётся»).")}
    <h3>Почему факт ссылается на листинг, а не на продукт</h3>
    <p>Листинг — единственная точка, где сходятся <strong>SKU + канал + рынок</strong>. Сослав факт на листинг,
    мы одной ссылкой сохраняем всю атрибуцию: какой вариант, где и через кого продан. Ссылка на продукт напрямую
    потеряла бы канал и рынок — и вся аналитика каналов и стран рассыпалась бы.</p>
    """
    B.append(chap(1,"Ядро онтологии: шесть уровней",
        "Почему концепт, вариант и размещение разделены — и почему это разделение обязательно.",b))

    # Глава 2
    b=f"""
    <p class="lead-in">У каждой связи есть <strong>направление</strong> (кто на кого ссылается) и
    <strong>кратность</strong> (один-ко-многим). Оба выбраны не случайно.</p>
    {fig(cardinality(),"<b>Схема 2.</b> Кратности ядра. Один продукт — много SKU; один SKU — много листингов; один листинг принадлежит ровно одному рынку и одному каналу. Тройка (SKU · Channel · Market) уникальна.")}
    <h3>Почему ссылается ребёнок, а не родитель</h3>
    <p>Ссылку всегда несёт <strong>сторона «многих»</strong>: SKU ссылается на product, listing — на sku.
    Так родитель не знает о детях и остаётся стабильным, а добавление ребёнка — это одна новая строка, без правки родителя.
    Обратное (список детей внутри родителя) раздувало бы родителя и ломало бы его при каждом новом варианте.</p>
    {wtable(["Связь","Кратность","Почему так"],[
     ["skus → products","∞ : 1","варианты специализируют концепт; концепт о них не знает"],
     ["listings → skus","∞ : 1","один SKU размещается многократно (разные каналы/рынки)"],
     ["listings → markets","∞ : 1","листинг локализован ровно в одном рынке (валюта, налог)"],
     ["listings → channels","∞ : 1","листинг продаётся ровно через один канал (своя комиссия)"],
     ["order_lines → listings","∞ : 1","много продаж одного размещения; факт всегда на стороне «многих»"],
    ])}
    {callout("why","Почему тройка уникальна","Если бы для одной пары «SKU + канал + рынок» существовало два листинга, "
     "стало бы неоднозначно, какая у неё цена и какой контент. Уникальность тройки делает листинг <b>адресом</b>: "
     "по нему всегда однозначно находятся цена (ценовой период), язык (контент) и комиссия (канал).")}
    """
    B.append(chap(2,"Связи ядра: направление и кратность",
        "Почему ссылку несёт сторона «многих» и почему тройка размещения уникальна.",b))

    # Глава 3
    b=f"""
    <p class="lead-in">Пять справочников датированы: <strong>price_periods, fx_rates, market_tax, cost_periods,
    channel_fees</strong>. Причина одна — витрины должны знать значение <strong>на дату факта</strong>, а не «сейчас».</p>
    {fig(price_timeline(),"<b>Схема 3.</b> Ценовые периоды. Цена сменилась 15-го. Заказ от 10-го ссылается на период $24.90, заказ от 16-го — на $27.90. История не затирается — обе цены остаются истиной своего интервала.")}
    <h3>Почему цена — не поле, а период</h3>
    <p>Если цена — просто поле листинга, то смена цены уничтожает прошлое: вчерашний заказ «задним числом»
    посчитается по новой цене, и недельная выручка исказится. Ценовой период с датами
    <code>valid_from … valid_to</code> хранит <strong>каждую цену как факт своего интервала</strong>.
    Заказ прибивается к тому периоду, что действовал в момент продажи (<code>order_lines.Price_Period_ID</code>).</p>
    {wtable(["Датированный справочник","Что фиксирует на дату","Что сломалось бы без даты"],[
     ["price_periods","цену листинга в интервале","выручка прошлых недель пересчиталась бы по новой цене"],
     ["fx_rates","курс к базовой валюте","маржа в базе поплыла бы при каждом движении курса"],
     ["market_tax","ставку налога рынка","старые заказы получили бы сегодняшнюю ставку НДС"],
     ["cost_periods","себестоимость SKU","маржа считалась бы по неверной закупке"],
     ["channel_fees","комиссию канала","пересмотр тарифа переписал бы историю комиссий"],
    ])}
    {callout("key","Паттерн «темпоральный join»","Чтобы получить значение на дату, берётся строка, где "
     "<code>valid_from ≤ дата_факта</code> и (<code>valid_to</code> пуст или <code>&gt; дата_факта</code>). "
     "Это единый приём для всех пяти справочников.")}
    {callout("imp","Важно","История — это <b>данные, а не ошибка</b>. Датированные справочники никогда не «чистятся»: "
     "новая цена/курс/ставка — это новая строка, а не правка старой.")}
    """
    B.append(chap(3,"Время в модели: почему всё датировано",
        "Почему цена, курс, налог и себестоимость живут интервалами, а заказ ссылается на «как было».",b))

    # Глава 4
    b=f"""
    <p class="lead-in">У каждого факта — <strong>ровно один дом</strong>. Дублирование запрещено не из эстетики:
    две копии неизбежно разъезжаются, и появляется две «истины».</p>
    {wtable(["Факт","Единственный дом","Почему не в другом месте"],[
     ["Цена","price_periods","на продукте/SKU она размножилась бы по рынкам и акциям"],
     ["Контент (название, описание)","listing_content","в продукте нельзя хранить N языков без дублей SKU"],
     ["Комиссия","channel_fees","привязана к каналу; на листинге — копия на каждый листинг канала"],
     ["Налог","market_tax","свойство рынка и времени, а не товара"],
     ["Себестоимость","cost_periods","свойство SKU во времени, а не строки заказа"],
    ])}
    <h3>Почему добавили таблицу себестоимости</h3>
    <p>Витрина маржи требует «− себестоимость», но в исходном ядре затрат не было. Спрятать их в строку заказа —
    значит потерять историю закупок и раздуть факт. Поэтому появился отдельный периодический справочник
    <code>cost_periods</code> — тем же паттерном, что и цена. Это <strong>единственная сущность, добавленная
    к исходной онтологии</strong>, и добавлена осознанно.</p>
    {callout("why","Почему единый дом важнее удобства","Скопировать цену «поближе, чтобы не джойнить» — это соблазн, "
     "который через месяц даёт две несовпадающие цены и вопрос «какая правильная». Один дом = одна истина. "
     "Джойн дешевле рассинхрона.")}
    """
    B.append(chap(4,"Единый дом факта: без дублирования",
        "Почему цена, контент, комиссия, налог и себестоимость живут каждый в одном месте.",b))

    # Глава 5
    b=f"""
    <p class="lead-in">Слой целей — дерево: <strong>Business → Marketing → {{Campaign · Channel · Test}}</strong>.
    Три типа целей существуют потому, что отвечают на три разных вопроса.</p>
    {fig(goals_tree(),"<b>Схема 4.</b> Дерево целей. Кампания меняет восприятие и поведение, канал качает эффективность, тест добывает знание. KPI берутся из словаря; факт результата (outcomes) отделён от плана (target).")}
    <h3>Почему три типа целей, а не один</h3>
    {wtable(["Тип цели","На что отвечает","Ключевые поля","Почему отдельно"],[
     ["Campaign","изменить восприятие/поведение аудитории","аудитория, желаемое изменение, тактики","у кампании есть смысл и адресат, а не только число"],
     ["Channel","поднять эффективность канала","baseline → target с датами, цикл оптимизации","канал — это петля оптимизации, а не разовая акция"],
     ["Test","закрыть неизвестность","гипотеза, порог, правило решения","тест обязан кончиться решением, иначе он не тест"],
    ])}
    <h3>Почему план и факт никогда не в одной ячейке</h3>
    <p>Target живёт в цели, факт — в <code>outcomes</code> (или считается из фактов по словарю). Держи их в одной
    ячейке — и нельзя ни сравнить план с фактом, ни увидеть дрейф во времени. Разделение делает возможной витрину
    «план vs факт, % выполнения, статус».</p>
    {callout("why","Почему KPI — словарь, а не текст","Каждый KPI (<code>kpi_definitions</code>) несёт формулу из фактовых "
     "таблиц и источник. KPI «свободным текстом» неаудируем: два человека посчитают ROAS по-разному. Словарь делает "
     "метрику <b>однозначной и воспроизводимой</b>.")}
    {callout("imp","Почему objective_scope полиморфен — и чем платим","Одна цель может касаться листингов, рынка и канала сразу, "
     "поэтому scope — мост «цель ↔ измерения» через (тип + ID). Плата: полиморфная ссылка не проверяется базой "
     "автоматически — её целостность держит дисциплина или разнесение на типовые таблицы при переносе на платформу.")}
    """
    B.append(chap(5,"Слой целей: план отделён от факта",
        "Почему три типа целей, почему KPI — словарь и почему outcomes никогда не в ячейке плана.",b))

    # Глава 6
    b=f"""
    <p class="lead-in">Факты <strong>append-only</strong>: не редактируются задним числом. Исправление — всегда
    новая строка. Это защищает истину о прошлом.</p>
    <h3>Почему заказ разбит на шапку и строки</h3>
    <p>Один заказ содержит несколько позиций. Шапка (<code>orders</code>) несёт общее — дату, канал, рынок,
    атрибуцию, статус; строки (<code>order_lines</code>) — конкретику: листинг, количество, цену на момент продажи,
    ценовой период. <strong>Грань факта — строка</strong>, потому что именно она привязана к листингу и цене.</p>
    {callout("key","Почему возврат — новая строка, а не удаление","Возврат заказа не стирает продажу — она была. "
     "Исходная строка (<code>L008</code>, +1) остаётся; корректировка — новая строка (<code>L008R</code>, −1) со статусом return. "
     "Витрина суммирует и даёт чистый ноль по единице, но <b>оба факта видны</b>. Так P&L уменьшается, а история цела.")}
    <h3>Почему остатки — на грани SKU × склад, а не листинга</h3>
    {fig(inventory(),"<b>Схема 5.</b> Единственное исключение из правила «факт → листинг». Физический сток общий для всех листингов SKU; привяжи остаток к листингу — и один и тот же запас посчитается несколько раз.")}
    <p>Это осознанное отступление от «факт ссылается на листинг»: сток физичен и общий. «Недели запаса по листингу»
    получаются разложением скорости продаж листингов обратно на их SKU.</p>
    <h3>Почему подписка — строки-периоды</h3>
    <p>Жизненный цикл (старт → продление → отмена) нельзя редактировать в одной строке, не теряя истории. Поэтому
    каждый биллинг-период — <strong>отдельная append-only строка</strong>; MRR-витрина суммирует активные периоды по
    месяцам без изменения схемы.</p>
    {callout("why","Почему у marketing_daily своя грань","Расход не привязан к строке заказа — он агрегирован по "
     "дате × каналу × кампании × рынку. Продажи (грань — строка) и расход (грань — день/канал) сходятся не на уровне "
     "листинга, а выше — на канале, кампании и рынке. Разные грани — это норма, а не ошибка; они мирятся в витрине.")}
    """
    B.append(chap(6,"Фактовый слой: append-only",
        "Почему факты исправляются строкой, почему остатки — исключение и почему у расхода своя грань.",b))

    # Глава 7
    b=f"""
    <p class="lead-in">Путь от сырого события до решения — один и тот же для всей компании.</p>
    {fig(flow(),"<b>Схема 6.</b> Событие → факт (append-only) → каталог KPI (единый источник истины и формул) → витрина → решение (всегда человек) → знание, которое возвращается в каталог и playbook.")}
    <h3>Почему витрины считают, а не хранят</h3>
    <p>Витрина (P&L, ROAS, статус целей, недели запаса) — <strong>представление, а не таблица</strong>. Хранить в ней
    числа значило бы завести вторую истину, которая разъедется с фактами. Витрина каждый раз пересобирается из фактов
    по формуле из словаря KPI — поэтому она всегда согласована с реальностью и с планом.</p>
    {callout("key","Почему два потока не сводятся","Поток-1 (личные продажи, ₽/£) и поток-2 (воронка) имеют разную "
     "экономику. В модели они разведены <b>разрезом по каналу и базовой валюте</b>: ни одна витрина не складывает их в "
     "одно число. Это то же жёсткое правило, что и во всём проекте.")}
    <p>Тот же путь питает борды MMS: слой фактов → каталог KPI → витрины — это и есть недостающий Data Dictionary,
    к которому борды обращаются за метриками.</p>
    """
    B.append(chap(7,"От события к решению",
        "Почему витрины считают из фактов, а не хранят числа, и почему потоки не сводятся.",b))

    # Глава 8
    b=f"""
    <p class="lead-in">Обратная сторона «почему так» — «почему не иначе». Ниже — соблазны, каждый из которых
    сначала кажется проще, а потом ломает систему.</p>
    {wtable(["Соблазн","Почему ломается","Что делаем вместо","cls"],[],"anti")}
    {wtable(["Соблазн (как «проще»)","Почему ломается","Что делаем вместо"],[
     ["Цена — поле продукта","на 2-й стране — много цен и валют; акция плодит копии продукта","цена на листинге, в ценовых периодах"],
     ["Одна большая плоская таблица","теряются история, атрибуция канала/рынка, растёт дублирование","нормализация: ядро + справочники + факты"],
     ["KPI «свободным текстом»","два человека считают по-разному; метрика неаудируема","словарь kpi_definitions с формулой из фактов"],
     ["Править факт задним числом","истина о прошлом стирается; отчёты «плывут»","append-only: исправление — новая строка (сторно/возврат)"],
     ["Остаток на листинге","общий сток задваивается по листингам SKU","остаток на SKU × склад; листинг — разложением"],
     ["Свести два потока в одну витрину","смешивается разная экономика → ложные выводы","разрез по каналу и базовой валюте, никогда не суммировать"],
     ["План и факт в одной ячейке","нельзя сравнить и увидеть дрейф","target — в цели, факт — в outcomes/фактах"],
    ],"anti")}
    {callout("anti","Общий корень всех ошибок","Каждый анти-паттерн — это попытка сэкономить на разделении: "
     "смешать концепт с ценой, план с фактом, справочник с событием, два потока в одно число. Модель дороже в момент "
     "записи (нужен джойн), но <b>единственно честна</b> в момент вопроса.")}
    """
    # первая пустая wtable убрана — оставляем только заполненную
    b=b.replace(wtable(["Соблазн","Почему ломается","Что делаем вместо","cls"],[],"anti"),"")
    B.append(chap(8,"Почему НЕ иначе: анти-паттерны",
        "Соблазн «сделать проще» → почему он ломается → что делаем вместо.",b))

    # Приложение
    b=f"""
    <p class="lead-in">Все 44 связи модели сводятся к <strong>шести формам отношений</strong>. Понимаешь шесть
    паттернов — понимаешь всю схему.</p>
    {wtable(["Паттерн","Члены (примеры)","Кратность","Зачем эта форма"],[
     ["1 · Иерархия «родитель → дети»","skus→products; marketing→business; campaign/channel/test→marketing","∞ : 1","специализация; ребёнок ссылается на родителя"],
     ["2 · Тройка размещения","listings → skus, channels, markets","три ∞ : 1","делает листинг уникальным адресом продажи"],
     ["3 · Темпоральная привязка","price_periods, fx_rates, market_tax, cost_periods, channel_fees → измерение + даты","∞ : 1 во времени","значение «на дату факта», история не затирается"],
     ["4 · Локализация/детализация","listing_content → listings + languages","∞ : 1 (× язык)","N версий контента на один листинг без дублей SKU"],
     ["5 · Мост M:N","campaign_channels, campaign_supporting_metrics, objective_scope","многие : многим","связь «многие-ко-многим» через промежуточную таблицу"],
     ["6 · Факт → измерение","order_lines→listing/price_period; orders→channel/market/campaign; marketing_daily→…; inventory→sku/warehouse","∞ : 1","факт ссылается на справочники, никогда наоборот"],
    ])}
    {callout("key","Как этим пользоваться","Встречаешь новую связь — определи её паттерн. Если это факт, он обязан "
     "ссылаться на измерение (паттерн 6), а не наоборот. Если это значение во времени — оно идёт в датированный "
     "справочник (паттерн 3). Если «многие-ко-многим» — только через мост (паттерн 5). Новых форм не изобретаем.")}
    <div class="divider"><span class="d"></span></div>
    <p class="small">Полная схема, поля всех таблиц, демо-данные и прогон приёмки — в
    <code>docs/10-data-model.md</code>. Интерактивная версия — <code>data-model.html</code> (GitHub Pages).
    Бриф для C-level — отдельный документ.</p>
    """
    B.append(chap("A","Приложение: шесть паттернов связей",
        "Вся модель — это шесть повторяющихся форм отношений.",b))

    return "<!doctype html><html lang='ru'><head><meta charset='utf-8'><style>"+CSS+"</style></head><body>"+"".join(B)+"</body></html>"

def main():
    os.makedirs(OUT_DIR,exist_ok=True)
    doc=build()
    open(os.path.join(OUT_DIR,"manual-source.html"),"w",encoding="utf-8").write(doc)
    pdf=os.path.join(OUT_DIR,PDF_NAME)
    HTML(string=doc,base_url=OUT_DIR).write_pdf(pdf)
    print("PDF:",pdf,os.path.getsize(pdf),"bytes")

if __name__=="__main__":
    main()
