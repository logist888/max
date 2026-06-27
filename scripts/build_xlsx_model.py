# -*- coding: utf-8 -*-
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule
from openpyxl.utils import get_column_letter

wb = Workbook()

# ---- styles ----
BLUE="2463EB"; DARK="101827"; PINK="FA2F6B"; SKY="6AC2EA"
hdr_fill=PatternFill("solid", fgColor=BLUE)
sub_fill=PatternFill("solid", fgColor="EEF4FF")
inp_fill=PatternFill("solid", fgColor="C9D7F5")   # editable inputs
fact_fill=PatternFill("solid", fgColor="FFF2CC")  # fact (user)
tot_fill=PatternFill("solid", fgColor="F3F4F6")
red=PatternFill("solid", fgColor="FFC7CE"); redf=Font(color="9C0006")
yel=PatternFill("solid", fgColor="FFEB9C"); yelf=Font(color="9C6500")
grn=PatternFill("solid", fgColor="C6EFCE"); grnf=Font(color="006100")
white_b=Font(bold=True, color="FFFFFF")
bold=Font(bold=True, color=DARK)
grey=Font(color="6B7280")
title_f=Font(bold=True, size=14, color=DARK)
note_f=Font(italic=True, size=9, color="6B7280")
thin=Side(style="thin", color="E5E7EB")
border=Border(left=thin,right=thin,top=thin,bottom=thin)
RUB='#,##0\\ ₽'; USD='$#,##0.00'; PCT='0.0%'; NUM='#,##0.0'; INT='#,##0'

def style_hdr(ws, row, ncols, start=1):
    for c in range(start, start+ncols):
        cell=ws.cell(row=row, column=c); cell.fill=hdr_fill; cell.font=white_b
        cell.alignment=Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border=border

def title(ws, text, span):
    ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=span)
    c=ws.cell(row=1,column=1,value=text); c.font=title_f
    c.alignment=Alignment(vertical="center")
    ws.row_dimensions[1].height=24

# =====================================================================
# ПАРАМЕТРЫ (editable inputs)
# =====================================================================
wp = wb.active; wp.title="Параметры"
title(wp,"⚙ Параметры модели — редактируемые входные данные (синие ячейки)",3)
wp.cell(row=2,column=1,value="Показатель").font=bold
wp.cell(row=2,column=2,value="Значение").font=bold
wp.cell(row=2,column=3,value="Ед. / примечание").font=bold
style_hdr(wp,2,3)

params=[
 ("Курс доллара", 80, "₽ / $ — меняешь здесь, пересчитывается вся модель", USD if False else INT),
 ("Бюджет VK", 1000, "$ за цикл", INT),
 ("Бюджет Meta", 1000, "$ за цикл", INT),
 ("CPC VK", 0.34, "$ за клик", USD),
 ("CPC Meta", 0.675, "$ за клик (диаспора/MENA дороже)", USD),
 ("Клик → старт скрининга, VK", 0.40, "доля", PCT),
 ("Клик → старт скрининга, Meta", 0.425, "доля", PCT),
 ("Старт → завершение скрининга", 0.48, "доля (≈18 вопросов + e-mail до результата)", PCT),
 ("Завершивший → покупка 50К  ⚠СТАВКА", 0.003, "доля — гипотеза скрининга, НЕ валидирована", PCT),
 ("Цена «Профориентация 50К»", 50000, "₽ — живой CTA Потока 2", RUB),
 ("Цена подписки Pro", 2990, "₽ / мес", RUB),
 ("Цена подписки Ultima", 9990, "₽ / мес", RUB),
 ("Подписки Pro за цикл", 4, "шт (первый платёж)", INT),
 ("Подписки Ultima за цикл", 1, "шт (первый платёж)", INT),
 ("Часы эксперта на отчёт", 1.5, "ч — узкое место (этап 5)", NUM),
 ("Ставка эксперта", 2000, "₽ / ч", RUB),
 ("Стоимость ИИ-отчёта", 300, "₽ (API)", RUB),
 ("Эквайринг", 0.04, "доля от чека", PCT),
 ("Постоянные: Meta-специалист", 600, "$ / мес", INT),
 ("Постоянные: инструменты/сервисы", 150, "$ / мес", INT),
 ("Постоянные: операционные/накладные", 30000, "₽ / мес", RUB),
 ("Цель компании", 1000000, "$ (валовая выручка)", INT),
 ("Горизонт цели", 6, "мес", INT),
]
keys=["FX","BUD_VK","BUD_META","CPC_VK","CPC_META","S_VK","S_META","COMPLETE","PURCH",
      "P50","PPRO","PULT","N_PRO","N_ULT","EXP_H","EXP_R","AI_C","ACQ",
      "FIX_META","FIX_TOOLS","FIX_OPS","GOAL_USD","GOAL_MONTHS"]
P={}
r=3
for (lbl,val,note,fmt),key in zip(params,keys):
    wp.cell(row=r,column=1,value=lbl).font=Font(color=DARK)
    vc=wp.cell(row=r,column=2,value=val); vc.fill=inp_fill; vc.font=bold; vc.number_format=fmt; vc.border=border
    wp.cell(row=r,column=3,value=note).font=note_f
    P[key]=f"Параметры!$B${r}"
    r+=1
wp.column_dimensions['A'].width=40; wp.column_dimensions['B'].width=14; wp.column_dimensions['C'].width=52
wp.freeze_panes="A3"

# =====================================================================
# МАРКЕТИНГ (план-факт)
# =====================================================================
wm=wb.create_sheet("Маркетинг")
title(wm,"📊 Маркетинговый борт — воронка Потока 2, план / факт",8)
heads=["Показатель","VK план","Meta план","Итого план","VK факт","Meta факт","Итого факт","Δ Итого (факт−план)"]
for i,h in enumerate(heads,1): wm.cell(row=2,column=i,value=h)
style_hdr(wm,2,8)
# rows: track addresses
mr={}
def mrow(rn, name, vk, meta, tot, fmt=INT, fact=True, delta=True):
    wm.cell(row=rn,column=1,value=name).font=Font(color=DARK)
    if vk is not None:
        c=wm.cell(row=rn,column=2,value=vk); c.number_format=fmt; c.border=border
    if meta is not None:
        c=wm.cell(row=rn,column=3,value=meta); c.number_format=fmt; c.border=border
    c=wm.cell(row=rn,column=4,value=tot); c.number_format=fmt; c.border=border; c.font=bold
    if fact:
        for col in (5,6,7):
            fc=wm.cell(row=rn,column=col); fc.fill=fact_fill; fc.number_format=fmt; fc.border=border
    if delta:
        dc=wm.cell(row=rn,column=8,value=f"=G{rn}-D{rn}"); dc.number_format=fmt; dc.border=border
    return rn
r=3
mr['bud']=r; mrow(r,"Бюджет, ₽", f"={P['BUD_VK']}*{P['FX']}", f"={P['BUD_META']}*{P['FX']}", f"=B{r}+C{r}", RUB); r+=1
mr['clk']=r; mrow(r,"Клики", f"={P['BUD_VK']}/{P['CPC_VK']}", f"={P['BUD_META']}/{P['CPC_META']}", f"=B{r}+C{r}", INT); r+=1
mr['st']=r;  mrow(r,"Старты скрининга", f"=B{mr['clk']}*{P['S_VK']}", f"=C{mr['clk']}*{P['S_META']}", f"=B{r}+C{r}", INT); r+=1
mr['ld']=r;  mrow(r,"Завершённые скрининги = лиды (e-mail)", f"=B{mr['st']}*{P['COMPLETE']}", f"=C{mr['st']}*{P['COMPLETE']}", f"=B{r}+C{r}", INT); r+=1
mr['cpl']=r; mrow(r,"CPL, $", f"={P['BUD_VK']}/B{mr['ld']}", f"={P['BUD_META']}/C{mr['ld']}", f"=({P['BUD_VK']}+{P['BUD_META']})/D{mr['ld']}", USD); r+=1
mr['sl']=r;  mrow(r,"Продажи «Профориентация 50К»  ⚠СТАВКА", f"=B{mr['ld']}*{P['PURCH']}", f"=C{mr['ld']}*{P['PURCH']}", f"=B{r}+C{r}", NUM); r+=1
mr['r50']=r; mrow(r,"Выручка 50К, ₽", f"=B{mr['sl']}*{P['P50']}", f"=C{mr['sl']}*{P['P50']}", f"=B{r}+C{r}", RUB); r+=1
mr['rsub']=r; mrow(r,"Выручка подписок, ₽", None, None, f"={P['N_PRO']}*{P['PPRO']}+{P['N_ULT']}*{P['PULT']}", RUB); r+=1
mr['rev']=r; mrow(r,"Выручка всего, ₽", f"=B{mr['r50']}", f"=C{mr['r50']}", f"=D{mr['r50']}+D{mr['rsub']}", RUB); r+=1
mr['drr']=r; mrow(r,"ДРР (реклама ₽ / выручка ₽)", f"=B{mr['bud']}/B{mr['rev']}", f"=C{mr['bud']}/C{mr['rev']}", f"=D{mr['bud']}/D{mr['rev']}", PCT); r+=1
# ДРР traffic light on B..D and G
for col in ('B','C','D'):
    rng=f"{col}{mr['drr']}"
    wm.conditional_formatting.add(rng, CellIsRule(operator="greaterThan", formula=["1"], fill=red, font=redf))
    wm.conditional_formatting.add(rng, CellIsRule(operator="between", formula=["0.5","1"], fill=yel, font=yelf))
    wm.conditional_formatting.add(rng, CellIsRule(operator="lessThan", formula=["0.5"], fill=grn, font=grnf))
note_r=r+1
wm.cell(row=note_r,column=1,value="Жёлтые ячейки «факт» — для ваших фактических чисел; Δ считается автоматически. ДРР: 🟢<50% · 🟡50–100% · 🔴>100%. «Продажи 50К» дробные — матожидание, фактический исход цикла 0–3.").font=note_f
wm.merge_cells(start_row=note_r,start_column=1,end_row=note_r,end_column=8)
widths=[42,12,12,13,11,11,12,18]
for i,w in enumerate(widths,1): wm.column_dimensions[get_column_letter(i)].width=w
wm.freeze_panes="B3"

# =====================================================================
# ЮНИТ-ЭКОНОМИКА
# =====================================================================
wu=wb.create_sheet("Юнит-экономика")
title(wu,"💸 Юнит-экономика «Профориентация 50 000 ₽» (Поток 2)",3)
wu.cell(row=2,column=1,value="Показатель").font=bold
wu.cell(row=2,column=2,value="Значение").font=bold
wu.cell(row=2,column=3,value="Формула / примечание").font=bold
style_hdr(wu,2,3)
ur={}
def urow(rn,name,formula,fmt,note=""):
    wu.cell(row=rn,column=1,value=name).font=Font(color=DARK)
    c=wu.cell(row=rn,column=2,value=formula); c.number_format=fmt; c.border=border; c.font=bold
    wu.cell(row=rn,column=3,value=note).font=note_f
    return rn
r=3
ur['price']=r; urow(r,"Цена", f"={P['P50']}", RUB,"живой CTA Потока 2"); r+=1
ur['var']=r;   urow(r,"Переменные на сделку, ₽", f"={P['EXP_H']}*{P['EXP_R']}+{P['AI_C']}+{P['P50']}*{P['ACQ']}", RUB,"проверка эксперта + ИИ + эквайринг"); r+=1
ur['cm']=r;    urow(r,"CM (вклад на сделку), ₽", f"=B{ur['price']}-B{ur['var']}", RUB,"цена − переменные"); r+=1
ur['cmp']=r;   urow(r,"CM, %", f"=B{ur['cm']}/B{ur['price']}", PCT,""); r+=1
ur['cmh']=r;   urow(r,"CM на человеко-час эксперта, ₽/ч", f"=B{ur['cm']}/{P['EXP_H']}", RUB,"цена узкого места (этап 5)"); r+=1
ur['fix']=r;   urow(r,"Постоянные за цикл, ₽", f"={P['FIX_META']}*{P['FX']}+{P['FIX_TOOLS']}*{P['FX']}+{P['FIX_OPS']}", RUB,"Meta-спец + инструменты + накладные"); r+=1
ur['adv']=r;   urow(r,"Реклама за цикл, ₽", f"=({P['BUD_VK']}+{P['BUD_META']})*{P['FX']}", RUB,""); r+=1
ur['be_fix']=r; urow(r,"Безубыточность (покрыть постоянные), сделок", f"=B{ur['fix']}/B{ur['cm']}", NUM,""); r+=1
ur['be_all']=r; urow(r,"Безубыточность (реклама + постоянные), сделок", f"=(B{ur['adv']}+B{ur['fix']})/B{ur['cm']}", NUM,"сколько продаж 50К нужно «в плюс»"); r+=1
wu.column_dimensions['A'].width=46; wu.column_dimensions['B'].width=16; wu.column_dimensions['C'].width=44
wu.freeze_panes="A3"

# =====================================================================
# P&L КОМПАНИИ (план-факт, по потокам)
# =====================================================================
wl=wb.create_sheet("P&L компании")
title(wl,"📈 P&L компании — план / факт, потоки раздельно",7)
heads=["Статья, ₽","Поток 2 план","Поток 2 факт","Поток 1 план","Поток 1 факт","Компания план","Компания факт"]
for i,h in enumerate(heads,1): wl.cell(row=2,column=i,value=h)
style_hdr(wl,2,7)
lr={}
def lrow(rn,name,p2,fmt=RUB,total=True,bold_row=False,fact_p1=True):
    cc=wl.cell(row=rn,column=1,value=name); cc.font=bold if bold_row else Font(color=DARK)
    c=wl.cell(row=rn,column=2,value=p2); c.number_format=fmt; c.border=border
    wl.cell(row=rn,column=3).fill=fact_fill; wl.cell(row=rn,column=3).number_format=fmt; wl.cell(row=rn,column=3).border=border  # П2 факт
    d=wl.cell(row=rn,column=4); d.fill=fact_fill; d.number_format=fmt; d.border=border  # П1 план (manual)
    e=wl.cell(row=rn,column=5); e.fill=fact_fill; e.number_format=fmt; e.border=border  # П1 факт
    f=wl.cell(row=rn,column=6,value=f"=B{rn}+D{rn}"); f.number_format=fmt; f.border=border; f.font=bold
    g=wl.cell(row=rn,column=7,value=f"=C{rn}+E{rn}"); g.number_format=fmt; g.border=border
    return rn
r=3
lr['r50']=r; lrow(r,"Выручка 50К / профориентация", f"=Маркетинг!D{mr['r50']}"); r+=1
lr['rsub']=r; lrow(r,"Выручка подписок", f"=Маркетинг!D{mr['rsub']}"); r+=1
lr['rev']=r; lrow(r,"Выручка ИТОГО", f"=B{lr['r50']}+B{lr['rsub']}", bold_row=True); r+=1
lr['adv']=r; lrow(r,"− Реклама", f"=-({P['BUD_VK']}+{P['BUD_META']})*{P['FX']}"); r+=1
lr['var']=r; lrow(r,"− Переменные (по проданным отчётам)", f"=-Маркетинг!D{mr['sl']}*'Юнит-экономика'!B{ur['var']}"); r+=1
lr['contr']=r; lrow(r,"= Контрибуция", f"=B{lr['rev']}+B{lr['adv']}+B{lr['var']}", bold_row=True); r+=1
lr['fix']=r; lrow(r,"− Постоянные", f"=-('Юнит-экономика'!B{ur['fix']})"); r+=1
lr['op']=r; lrow(r,"= Операционный результат", f"=B{lr['contr']}+B{lr['fix']}", bold_row=True); r+=1
lr['drr']=r; lrow(r,"ДРР (реклама / выручка)", f"=-B{lr['adv']}/B{lr['rev']}", fmt=PCT); r+=1
lr['romi']=r; lrow(r,"ROMI (опер. результат / реклама)", f"=B{lr['op']}/-B{lr['adv']}", fmt=PCT); r+=1
# traffic lights on operating result & contribution (B,F,C,G)
for col in ('B','C','F','G'):
    for rr in (lr['op'],lr['contr']):
        wl.conditional_formatting.add(f"{col}{rr}", CellIsRule(operator="lessThan", formula=["0"], fill=red, font=redf))
        wl.conditional_formatting.add(f"{col}{rr}", CellIsRule(operator="greaterThanOrEqual", formula=["0"], fill=grn, font=grnf))
for col in ('B','F'):
    rr=lr['drr']
    wl.conditional_formatting.add(f"{col}{rr}", CellIsRule(operator="greaterThan", formula=["1"], fill=red, font=redf))
    wl.conditional_formatting.add(f"{col}{rr}", CellIsRule(operator="between", formula=["0.5","1"], fill=yel, font=yelf))
    wl.conditional_formatting.add(f"{col}{rr}", CellIsRule(operator="lessThan", formula=["0.5"], fill=grn, font=grnf))
nr=r+1
wl.cell(row=nr,column=1,value="Поток 1 (HNW, личные продажи Макса) — жёлтые ячейки заполняются вручную, в воронку Потока 2 не входит. Жёлтое = ввод. 🔴 опер. результат < 0.").font=note_f
wl.merge_cells(start_row=nr,start_column=1,end_row=nr,end_column=7)
widths=[34,14,14,14,14,15,15]
for i,w in enumerate(widths,1): wl.column_dimensions[get_column_letter(i)].width=w
wl.freeze_panes="B3"

# =====================================================================
# ДАШБОРД КОМПАНИИ
# =====================================================================
wd=wb.create_sheet("Дашборд компании")
wb.move_sheet("Дашборд компании", -(len(wb.sheetnames)-1))  # move to front
title(wd,"🏢 Дашборд компании MainExperts — цель, воронка, P&L (план / факт)",5)
wd.cell(row=2,column=1,value="Все числа считаются формулами от листа «Параметры» (курс $ = 80). Синее — входные данные, жёлтое — ваш факт.").font=note_f
wd.merge_cells(start_row=2,start_column=1,end_row=2,end_column=5)

# --- Цель компании ---
gr=4
wd.cell(row=gr,column=1,value="🎯 ЦЕЛЬ КОМПАНИИ").font=Font(bold=True,size=12,color=BLUE)
wd.merge_cells(start_row=gr,start_column=1,end_row=gr,end_column=5)
gh=gr+1
for i,h in enumerate(["Показатель","Значение","",""],1): wd.cell(row=gh,column=i,value=h)
style_hdr(wd,gh,2)
g=gh+1
def drow(rn,name,formula,fmt,fill=None,fnt=None):
    wd.cell(row=rn,column=1,value=name).font=Font(color=DARK)
    c=wd.cell(row=rn,column=2,value=formula); c.number_format=fmt; c.border=border; c.font=fnt or bold
    if fill: c.fill=fill
    return rn
dg={}
dg['goal_usd']=g; drow(g,"Цель, $", f"={P['GOAL_USD']}", INT); g+=1
dg['goal_rub']=g; drow(g,"Цель, ₽ (× курс)", f"={P['GOAL_USD']}*{P['FX']}", RUB); g+=1
dg['goal_m']=g; drow(g,"Цель в месяц, ₽", f"=B{dg['goal_rub']}/{P['GOAL_MONTHS']}", RUB); g+=1
dg['rev_cycle']=g; drow(g,"Выручка / цикл (план, компания)", f"='P&L компании'!F{lr['rev']}", RUB); g+=1
dg['rev_fact']=g; drow(g,"Накопленная выручка (факт) ✎", None, RUB, fill=fact_fill); g+=1
dg['prog']=g; drow(g,"% достижения цели (факт)", f"=B{dg['rev_fact']}/B{dg['goal_rub']}", PCT); g+=1
dg['need_sales']=g; drow(g,"Продаж 50К для цели (если только 50К)", f"=B{dg['goal_rub']}/{P['P50']}", INT); g+=1
dg['need_day']=g; drow(g,"…в день (× горизонт)", f"=B{dg['need_sales']}/({P['GOAL_MONTHS']}*30)", NUM); g+=1
wd.cell(row=g,column=1,value="Потолок ручной проверки отчёта ≈ 9–10/день — выше этого цель упирается в узкое место (этап 5).").font=note_f
wd.merge_cells(start_row=g,start_column=1,end_row=g,end_column=5); g+=1
wd.conditional_formatting.add(f"B{dg['prog']}", ColorScaleRule(start_type='num',start_value=0,start_color='FFC7CE',
                              mid_type='num',mid_value=0.5,mid_color='FFEB9C', end_type='num',end_value=1,end_color='C6EFCE'))

# --- KPI цикла (план/факт) ---
k0=g+1
wd.cell(row=k0,column=1,value="📌 KPI ЦИКЛА ($2000: 1000 VK + 1000 Meta)").font=Font(bold=True,size=12,color=BLUE)
wd.merge_cells(start_row=k0,start_column=1,end_row=k0,end_column=5)
kh=k0+1
for i,h in enumerate(["Метрика","План","Факт","Δ (факт−план)","Светофор/примечание"],1): wd.cell(row=kh,column=i,value=h)
style_hdr(wd,kh,5)
k=kh+1
def krow(rn,name,plan,fmt,fact_default=None,light=None,note=""):
    wd.cell(row=rn,column=1,value=name).font=Font(color=DARK)
    c=wd.cell(row=rn,column=2,value=plan); c.number_format=fmt; c.border=border; c.font=bold
    fc=wd.cell(row=rn,column=3); fc.fill=fact_fill; fc.number_format=fmt; fc.border=border
    if fact_default is not None: fc.value=fact_default
    dc=wd.cell(row=rn,column=4,value=f"=C{rn}-B{rn}"); dc.number_format=fmt; dc.border=border
    wd.cell(row=rn,column=5,value=note).font=note_f
    return rn
dk={}
dk['bud']=k; krow(k,"Рекламный бюджет, ₽", f"=Маркетинг!D{mr['bud']}", RUB, note="вход = $2000 × курс"); k+=1
dk['leads']=k; krow(k,"Лиды (скрининги, e-mail)", f"=Маркетинг!D{mr['ld']}", INT, note="реальный актив бюджета"); k+=1
dk['cpl']=k; krow(k,"CPL, $", f"=Маркетинг!D{mr['cpl']}", USD); k+=1
dk['sales']=k; krow(k,"Продажи 50К", f"=Маркетинг!D{mr['sl']}", NUM, note="⚠ ставка на гипотезу скрининга"); k+=1
dk['rev']=k; krow(k,"Выручка, ₽", f"=Маркетинг!D{mr['rev']}", RUB); k+=1
dk['drr']=k; krow(k,"ДРР", f"=Маркетинг!D{mr['drr']}", PCT, note="🟢<50 · 🟡50–100 · 🔴>100"); k+=1
dk['op']=k; krow(k,"Операционный результат, ₽", f"='P&L компании'!F{lr['op']}", RUB, note="🔴 < 0"); k+=1
# lights
wd.conditional_formatting.add(f"B{dk['drr']}", CellIsRule(operator="greaterThan", formula=["1"], fill=red, font=redf))
wd.conditional_formatting.add(f"B{dk['drr']}", CellIsRule(operator="between", formula=["0.5","1"], fill=yel, font=yelf))
wd.conditional_formatting.add(f"B{dk['drr']}", CellIsRule(operator="lessThan", formula=["0.5"], fill=grn, font=grnf))
for col in ('B','C'):
    wd.conditional_formatting.add(f"{col}{dk['op']}", CellIsRule(operator="lessThan", formula=["0"], fill=red, font=redf))
    wd.conditional_formatting.add(f"{col}{dk['op']}", CellIsRule(operator="greaterThanOrEqual", formula=["0"], fill=grn, font=grnf))
widths=[40,16,16,16,40]
for i,w in enumerate(widths,1): wd.column_dimensions[get_column_letter(i)].width=w
wd.sheet_view.showGridLines=False
wd.freeze_panes="A3"

# =====================================================================
# КОНТЕНТ-АТРИБУЦИЯ (план-факт по контенту: статья → продажи → ДРР)
# =====================================================================
wc=wb.create_sheet("Контент-атрибуция")
title(wc,"🧭 Контент-атрибуция — какая статья / тема / канал → продажи и ДРР (факт)",14)
ch=["Статья / URL","Тема","Слов","Канал","UTM","Показы","Клики","Лиды","CPL, $","Продажи 50К","Выручка, ₽","Расход, ₽","ДРР","Свет."]
for i,h in enumerate(ch,1): wc.cell(row=2,column=i,value=h)
style_hdr(wc,2,14)
examples=[
 ("/blog/professii-buduschego","Профессии будущего",1800,"VK","seo/prof-future",12400,520,210,"",1,50000,18000),
 ("/lp/5-voprosov","5 вопросов о талантах (лид-магнит)",600,"Meta","meta/lm-5q",48000,900,540,"",1,50000,38000),
 ("/lp/7-oshibok","7 ошибок родителей",900,"VK","vk/lm-7err",31000,610,380,"",0,0,16000),
]
r=3
firstr=r
for ex in examples:
    for i,v in enumerate(ex,1):
        cell=wc.cell(row=r,column=i,value=(v if v!="" else None)); cell.border=border
        if i in (1,2,3,4,5,6,7,8,10,11,12): cell.fill=fact_fill  # entry cells
    wc.cell(row=r,column=9,value=f"=IF(H{r}=0,0,(L{r}/{P['FX']})/H{r})").number_format=USD  # CPL $
    wc.cell(row=r,column=13,value=f"=IF(K{r}=0,\"\",L{r}/K{r})").number_format=PCT          # ДРР
    wc.cell(row=r,column=9).border=border; wc.cell(row=r,column=13).border=border
    r+=1
# a few blank fact rows
for _ in range(5):
    for i in range(1,15):
        cell=wc.cell(row=r,column=i); cell.border=border
        if i in (1,2,3,4,5,6,7,8,10,11,12): cell.fill=fact_fill
    wc.cell(row=r,column=9,value=f"=IF(H{r}=0,0,(L{r}/{P['FX']})/H{r})").number_format=USD
    wc.cell(row=r,column=13,value=f"=IF(K{r}=0,\"\",L{r}/K{r})").number_format=PCT
    r+=1
lastr=r-1
# totals
wc.cell(row=r,column=1,value="ИТОГО / сводный ДРР").font=bold
for col,letter in [(6,'F'),(7,'G'),(8,'H'),(10,'J'),(11,'K'),(12,'L')]:
    c=wc.cell(row=r,column=col,value=f"=SUM({letter}{firstr}:{letter}{lastr})"); c.number_format=INT if col in(6,7,8,10) else RUB; c.font=bold; c.border=border; c.fill=tot_fill
c=wc.cell(row=r,column=13,value=f"=IF(K{r}=0,\"\",L{r}/K{r})"); c.number_format=PCT; c.font=bold; c.border=border; c.fill=tot_fill
# ДРР conditional formatting on column M
wc.conditional_formatting.add(f"M{firstr}:M{r}", CellIsRule(operator="greaterThan", formula=["1"], fill=red, font=redf))
wc.conditional_formatting.add(f"M{firstr}:M{r}", CellIsRule(operator="between", formula=["0.5","1"], fill=yel, font=yelf))
wc.conditional_formatting.add(f"M{firstr}:M{r}", CellIsRule(operator="lessThan", formula=["0.5"], fill=grn, font=grnf))
wc.cell(row=r+2,column=1,value="Жёлтые ячейки — ваш факт по кампаниям. CPL и ДРР считаются сами. Сводный ДРР внизу = Σрасход / Σвыручка. Три строки — пример, замени своими.").font=note_f
wc.merge_cells(start_row=r+2,start_column=1,end_row=r+2,end_column=14)
cw=[26,26,7,9,16,10,9,9,9,12,13,12,9,7]
for i,w in enumerate(cw,1): wc.column_dimensions[get_column_letter(i)].width=w
wc.freeze_panes="A3"

# force Excel/Sheets to recalc formulas on open (no cached values written by openpyxl)
try:
    wb.calculation.fullCalcOnLoad=True
except Exception:
    from openpyxl.workbook.properties import CalcProperties
    wb.calculation=CalcProperties(fullCalcOnLoad=True)

# order: Дашборд, Параметры, Маркетинг, Контент, Юнит, P&L
order=["Дашборд компании","Параметры","Маркетинг","Контент-атрибуция","Юнит-экономика","P&L компании"]
wb._sheets.sort(key=lambda s: order.index(s.title))

out="/home/user/max/boards/model-borda-mainexperts.xlsx"
wb.save(out)
print("saved", out)
