#!/usr/bin/env python3
"""Оформление отчёта об объёме SEO-страниц (docs/26-seo-volume-report.md) в PDF.

Два стиля: wave (волны, бирюзовый) и corp (корпоративный годовой отчёт, синий).
Страницы A4 вертикальные; каждая таблица на одной странице, при необходимости
масштабируется под страницу.

Запуск: python3 scripts/build_seo_report.py wave|corp [выход.pdf]
"""
import sys, re, html, math, os, tempfile

SRC = os.path.join(os.path.dirname(__file__), '..', 'docs', '26-seo-volume-report.md')
E = html.escape

# ---------------------------------------------------------------- разбор md
def tables_after(text, heading):
    """Все таблицы markdown после заголовка до следующего заголовка того же или старшего уровня."""
    i = text.index(heading)
    lvl = len(re.match(r'#+', heading).group(0))
    rest = text[i + len(heading):]
    m = re.search(r'\n#{1,%d} ' % lvl, rest)
    block = rest[:m.start()] if m else rest
    out, cur = [], []
    for line in block.split('\n'):
        if line.strip().startswith('|'):
            cur.append(line)
        elif cur:
            out.append(cur); cur = []
    if cur: out.append(cur)
    return [parse_table(t) for t in out]

def parse_table(lines):
    rows = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip().strip('|').split('|')]
        if all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c): continue
        rows.append([clean(c) for c in cells])
    return rows

def clean(c):
    c = re.sub(r'\*\*(.+?)\*\*', r'\1', c)
    c = c.replace('`', '')
    return c

def num(s):
    s = s.replace(' ', ' ').replace('≤', '').replace('≥', '').replace('~', '').strip()
    if re.fullmatch(r'\d[\d ]*', s): return int(s.replace(' ', ''))
    return None

def fmt(n):
    return f'{n:,}'.replace(',', ' ')

# ---------------------------------------------------------------- данные
T = open(SRC, encoding='utf-8').read()
sc_base = tables_after(T, '### 2.1 Базовый сценарий')[0]
sc_soft = tables_after(T, '### 2.2 Мягкий сценарий')[0]
sc_hard = tables_after(T, '### 2.3 Жёсткий сценарий')[0]
sc_tot = tables_after(T, '### 2.3 Жёсткий сценарий')[-1]
year_tabs = tables_after(T, '### 2.4 T43: год набора и редакционные блоки')
reasons = tables_after(T, '## 3. Причины K2 (базовый сценарий)')
sens = tables_after(T, '## 4. Чувствительность')[0]
origin = tables_after(T, '## 5. Происхождение × назначение')
blind61 = tables_after(T, '### 6.1 `noindex` из-за цены, срока подачи или текста')[0]
blind62 = tables_after(T, '### 6.2 Дубли родителя (K3)')[0]
locales = tables_after(T, '### 6.5 Локали')[0]
consist = tables_after(T, '### 6.6 Согласованность чисел (R-4.4.11)')[0]
matrix_cmp = tables_after(T, '### 7.1 Сверка с матрицей (шаг 1)')[0]

def split_scenario(tab):
    """-> (counted_rows, not_counted_rows). Строка учитывается в итоге, если все 6 чисел целые."""
    hdr, body = tab[0], tab[1:]
    counted, other = [], []
    for r in body:
        if r[0].startswith('Итого'): continue
        if all(num(x) is not None for x in r[2:8]) and not r[0].startswith('T40'):
            counted.append(r)
        else:
            other.append(r)
    return counted, other

COLS = ['Возможных', 'K1', 'K2', 'K3', 'K4', 'K5']
def totals(rows):
    t = [0] * 6
    for r in rows:
        for i in range(6): t[i] += num(r[2 + i])
    return t

# ---------------------------------------------------------------- стили
STYLES = {
 'wave': dict(
    name='wave', font="'Inter','DejaVu Sans',Arial,sans-serif",
    c1='#1fb5c9', c2='#9ad8c1', c3='#e6f4a8', ink='#46525d', soft='#7b8791', line='#d4e4e8',
    head_bg='#1fb5c9', head_fg='#ffffff', hi='#d9f3ee', hi2='#f1fafa', zebra='#f6fbfc', tot_bg='#e3f4f7',
    ok='#1fb5c9', warn='#f2a13b', bad='#e0575b', pal=['#1fb5c9', '#52c6b6', '#9ad8c1', '#c9e8a6', '#f2a13b', '#b8c6cc']),
 'corp': dict(
    name='corp', font="'Inter','DejaVu Sans',Arial,sans-serif",
    c1='#2b5ea7', c2='#8cc63f', c3='#d7e3f4', ink='#22314a', soft='#6f7f96', line='#c8d4e6',
    head_bg='#2b5ea7', head_fg='#ffffff', hi='#dff0c9', hi2='#eef6e2', zebra='#f2f6fb', tot_bg='#dbe6f5',
    ok='#2b5ea7', warn='#8cc63f', bad='#d0443a', pal=['#2b5ea7', '#5a82bd', '#98b2d6', '#c3d3e9', '#8cc63f', '#b3bfcf']),
}

def css(s):
    return f"""
@page {{ size: 210mm 297mm; margin: 0 }}
* {{ box-sizing: border-box }}
html, body {{ margin: 0; padding: 0; font-family: {s['font']}; color: {s['ink']}; -webkit-print-color-adjust: exact; print-color-adjust: exact }}
.page {{ width: 210mm; height: 297mm; position: relative; overflow: hidden; page-break-after: always; background: #fff; display: flex; flex-direction: column; padding: 15mm 15mm 14mm 15mm }}
.page:last-child {{ page-break-after: auto }}
h1 {{ font-size: 21pt; line-height: 1.15; margin: 0 0 3mm; color: {s['c1']}; font-weight: 600 }}
h2 {{ font-size: 12pt; margin: 0 0 2mm; color: {s['c1']}; font-weight: 700 }}
h3 {{ font-size: 10pt; margin: 0 0 1.5mm; color: {s['ink']}; font-weight: 700 }}
p {{ font-size: 9.2pt; line-height: 1.45; margin: 0 0 2.5mm }}
.lead {{ font-size: 10.5pt; line-height: 1.45; color: {s['soft']}; margin: 0 0 4mm }}
.small {{ font-size: 7.8pt; color: {s['soft']}; line-height: 1.4 }}
.fitbox {{ flex: 1 1 auto; min-height: 0; overflow: hidden; position: relative }}
.fit {{ transform-origin: top left; width: 100% }}
table {{ border-collapse: collapse; width: 100%; font-size: 8.6pt; font-variant-numeric: tabular-nums }}
th {{ background: {s['head_bg']}; color: {s['head_fg']}; font-weight: 600; text-align: right; padding: 1.6mm 2mm; font-size: 8.2pt }}
th.l, td.l {{ text-align: left }}
td {{ padding: 1.3mm 2mm; border-bottom: .2mm solid {s['line']}; text-align: right; vertical-align: top }}
table.dense td {{ padding: .6mm 1.5mm; font-size: 8.2pt }}
table.dense th {{ padding: 1mm 1.5mm; font-size: 7.8pt }}
tr.z td {{ background: {s['zebra']} }}
tr.idx td {{ background: {s['hi']}; font-weight: 600 }}
tr.idx2 td {{ background: {s['hi2']} }}
tr.grp td {{ background: #fff; color: {s['c1']}; font-weight: 700; text-align: left; font-size: 8pt; letter-spacing: .03em; text-transform: uppercase; padding-top: 2.2mm; border-bottom: .3mm solid {s['c1']} }}
tr.tot td {{ background: {s['tot_bg']}; font-weight: 700; border-top: .5mm solid {s['c1']}; border-bottom: none }}
tr.zero td.n0 {{ color: #b0b8c0 }}
td.code {{ font-weight: 700; color: {s['c1']}; text-align: left; white-space: nowrap }}
.tag {{ display: inline-block; font-size: 7pt; font-weight: 700; padding: .3mm 1.6mm; border-radius: 1mm; background: {s['c1']}; color: #fff; vertical-align: 1px }}
.sumbar {{ margin-top: 3mm; padding: 2.4mm 3.5mm; background: {s['tot_bg']}; border-left: 1.4mm solid {s['c1']}; font-size: 9.2pt; line-height: 1.5 }}
.sumbar b {{ color: {s['c1']} }}
.cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 3mm; margin: 2mm 0 4mm }}
.cards.two {{ grid-template-columns: repeat(2, 1fr) }}
.card {{ border: .3mm solid {s['line']}; border-radius: 2.5mm; padding: 3mm 3.5mm; background: #fff }}
.card .big {{ font-size: 20pt; font-weight: 700; color: {s['c1']}; line-height: 1.1 }}
.card .cap {{ font-size: 8.2pt; color: {s['soft']}; margin-top: 1mm; line-height: 1.35 }}
.k {{ display: flex; gap: 3mm; align-items: flex-start; margin-bottom: 2.4mm }}
.k .dot {{ flex: none; width: 11mm; height: 7mm; border-radius: 1.5mm; color: #fff; font-weight: 700; font-size: 9pt; display: flex; align-items: center; justify-content: center }}
.k div.t {{ font-size: 9pt; line-height: 1.4 }}
.k div.t b {{ color: {s['ink']} }}
ul {{ margin: 0 0 3mm; padding-left: 4.5mm; font-size: 9pt; line-height: 1.45 }}
li {{ margin-bottom: 1mm }}
.foot {{ position: absolute; left: 15mm; right: 15mm; bottom: 7mm; display: flex; justify-content: space-between; font-size: 7.5pt; color: {s['soft']} }}
.pn {{ font-weight: 700; color: {s['c2']} }}
.legend {{ display: flex; gap: 5mm; font-size: 8pt; color: {s['soft']}; margin: 0 0 3mm; flex-wrap: wrap }}
.legend i {{ display: inline-block; width: 4.5mm; height: 3mm; border-radius: .6mm; vertical-align: -.3mm; margin-right: 1.4mm }}
"""

# ---------------------------------------------------------------- оформление страниц
SECTIONS = ['Как читать', 'Итоги', 'Главная таблица', 'Сценарии', 'Год набора', 'Причины', 'Чувствительность', 'Происхождение × назначение', 'Слепые зоны', 'Что уже есть', 'Не найдено', 'Выводы']

def deco_wave(n, title_small):
    # декоративные волны по углам
    top = """<svg style="position:absolute;right:0;top:0" width="115mm" height="45mm" viewBox="0 0 300 120" preserveAspectRatio="none">
<defs><linearGradient id="g1" x1="0" x2="1"><stop offset="0" stop-color="#e6f4a8"/><stop offset="1" stop-color="#1fb5c9"/></linearGradient></defs>
<path d="M300 0 L300 90 C250 100 190 60 150 30 C120 8 90 0 70 0 Z" fill="url(#g1)" opacity=".5"/>
<path d="M300 0 L300 55 C260 70 215 40 185 18 C170 8 155 2 140 0 Z" fill="#ffffff" opacity=".55"/></svg>"""
    bot = """<svg style="position:absolute;left:0;bottom:0" width="90mm" height="26mm" viewBox="0 0 240 70" preserveAspectRatio="none">
<defs><linearGradient id="g2" x1="0" x2="1"><stop offset="0" stop-color="#1fb5c9"/><stop offset="1" stop-color="#e6f4a8"/></linearGradient></defs>
<path d="M0 70 L0 22 C40 8 90 30 130 48 C160 60 200 66 240 70 Z" fill="url(#g2)" opacity=".7"/></svg>"""
    return top + bot

def page_wrap(s, n, title_small, inner, no_deco=False, label=None):
    deco = deco_wave(n, title_small) if s['name'] == 'wave' else ''
    head = ''
    if s['name'] == 'corp':
        nav = ''.join(f'<div style="{"color:#2b5ea7;font-weight:700" if i == n else ""}">{("▸ " if i == n else "&nbsp;&nbsp;&nbsp;")}{E(x)}</div>' for i, x in enumerate(SECTIONS, 1) if abs(i - n) <= 2 or i in (1, len(SECTIONS)))
        head = f"""<div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:.35mm solid #2b5ea7;padding-bottom:3mm;margin-bottom:5mm">
<div style="font-size:34pt;font-weight:300;color:#2b5ea7;line-height:1">{label or f"{n}.0"}</div>
<div style="font-size:7pt;line-height:1.55;color:#6f7f96;text-transform:uppercase;letter-spacing:.04em;text-align:left;min-width:55mm">{nav}</div></div>"""
    else:
        head = f"""<div style="text-align:right;margin-bottom:5mm;position:relative;z-index:2">
<div style="font-size:8pt;letter-spacing:.18em;color:#46525d;font-weight:600">ОТЧЁТ</div>
<div style="font-size:15pt;color:#2d3a44;font-weight:700;line-height:1;text-shadow:0 0 3mm #fff">{E(title_small)}</div></div>"""
    return f"""<section class="page">{deco}{head}{inner}<div class="foot"><span>MainExperts · объём SEO-страниц · данные на 13.11.2026</span><span class="pn">{n if n else ''}</span></div></section>"""

def table_html(header, body, cls_rows=None, left_cols=2, tot=None, code_col=True, dense=False):
    th = ''.join(f'<th class="{"l" if i < left_cols else ""}">{E(h)}</th>' for i, h in enumerate(header))
    out = [f'<table class="{"dense" if dense else ""}"><thead><tr>{th}</tr></thead><tbody>']
    for k, r in enumerate(body):
        cls = ''
        if cls_rows and k in cls_rows: cls = cls_rows[k]
        elif k % 2: cls = 'z'
        if cls == 'grp':
            out.append(f'<tr class="grp"><td colspan="{len(header)}">{E(r[0])}</td></tr>'); continue
        tds = []
        for i, c in enumerate(r):
            c = str(c)
            if i == 0 and code_col: tds.append(f'<td class="code">{E(c)}</td>')
            elif i < left_cols: tds.append(f'<td class="l">{E(c)}</td>')
            else:
                v = num(c)
                n0 = ' n0' if v == 0 else ''
                tds.append(f'<td class="{(n0.strip() if v is not None else "l")}">{E(fmt(v)) if v is not None else E(c)}</td>')
        out.append(f'<tr class="{cls}">' + ''.join(tds) + '</tr>')
    if tot:
        out.append('<tr class="tot">' + ''.join(
            (f'<td class="l" colspan="{left_cols}">{E(tot[0])}</td>' if i == 0 else (f'<td>{E(fmt(v))}</td>' if isinstance(v, int) else f'<td>{E(str(v))}</td>'))
            for i, v in enumerate(tot) if i == 0 or i >= 1) + '</tr>')
    out.append('</tbody></table>')
    return ''.join(out)

def fit(inner):
    return f'<div class="fitbox"><div class="fit">{inner}</div></div>'

def donut(parts, size=46, hole=.58, colors=None):
    tot = sum(v for _, v in parts) or 1
    r = 40; cx = cy = 50; c = 2 * math.pi * r
    segs, off = [], 0
    for i, (lab, v) in enumerate(parts):
        frac = v / tot; length = c * frac
        segs.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{colors[i % len(colors)]}" stroke-width="{r * (1 - hole)}" stroke-dasharray="{length:.2f} {c - length:.2f}" stroke-dashoffset="{-off:.2f}" transform="rotate(-90 50 50)"/>')
        off += length
    return f'<svg width="{size}mm" height="{size}mm" viewBox="0 0 100 100">{"".join(segs)}</svg>'

def bars(items, color, width=170, label_w=34, maxv=None):
    maxv = maxv or max(v for _, v in items) or 1
    h = 6.2
    rows = []
    for i, (lab, v) in enumerate(items):
        y = i * h
        w = (width - label_w - 22) * v / maxv
        rows.append(f'<text x="0" y="{y + 4.4}" font-size="3.1" fill="#46525d">{E(lab)}</text><rect x="{label_w}" y="{y + 0.8}" width="{max(w, .4):.2f}" height="4" rx=".8" fill="{color}"/><text x="{label_w + w + 1.5:.2f}" y="{y + 4.4}" font-size="3.1" fill="#46525d">{E(fmt(v))}</text>')
    return f'<svg width="100%" viewBox="0 0 {width} {len(items) * h + 1}">{"".join(rows)}</svg>'

# ---------------------------------------------------------------- сборка
def build(style):
    s = STYLES[style]
    pages = []

    # --- расчёты по сценариям
    cnt_b, oth_b = split_scenario(sc_base)
    cnt_s, _ = split_scenario(sc_soft)
    cnt_h, _ = split_scenario(sc_hard)
    tb, ts, th_ = totals(cnt_b), totals(cnt_s), totals(cnt_h)
    names = {r[0]: r[1] for r in sc_base[1:]}
    # проверка: сумма классов = возможных
    check_b = tb[1] + tb[2] + tb[3] + tb[4] + tb[5]

    # --- 0. обложка
    if style == 'wave':
        cover = f"""<section class="page" style="padding:0">
<svg style="position:absolute;left:0;bottom:0" width="210mm" height="150mm" viewBox="0 0 210 150" preserveAspectRatio="none">
<defs><linearGradient id="c1" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#e6f4a8"/><stop offset=".55" stop-color="#9ad8c1"/><stop offset="1" stop-color="#1fb5c9"/></linearGradient>
<linearGradient id="c2" x1="1" x2="0"><stop offset="0" stop-color="#1fb5c9"/><stop offset="1" stop-color="#d2f0ef"/></linearGradient></defs>
<path d="M0 55 C45 20 120 20 210 62 L210 150 L0 150 Z" fill="url(#c1)"/>
<path d="M0 78 C50 45 130 45 210 88 L210 150 L0 150 Z" fill="url(#c2)" opacity=".75"/>
<path d="M0 110 C60 85 140 85 210 118 L210 150 L0 150 Z" fill="#ffffff" opacity=".55"/>
<circle cx="22" cy="140" r="34" fill="#ffffff"/></svg>
<div style="position:absolute;right:22mm;top:36mm;text-align:right">
<div style="font-size:12pt;letter-spacing:.22em;color:#46525d;font-weight:600">ОТЧЁТ</div>
<div style="font-size:36pt;font-weight:700;color:#46525d;line-height:1.05;margin-top:2mm">Объём<br>SEO-страниц</div>
<div style="font-size:54pt;font-weight:700;color:#1fb5c9;line-height:1.1;margin-top:3mm">2026</div></div>
<div style="position:absolute;left:18mm;bottom:20mm;color:#46525d"><div style="font-size:11pt;font-weight:700;letter-spacing:.08em">MAINEXPERTS</div>
<div style="font-size:9pt;margin-top:1mm">Счёт по базе портала<br>данные на 13.11.2026</div></div></section>"""
    else:
        cover = f"""<section class="page" style="padding:0;background:#fff">
<div style="position:absolute;left:0;top:0;width:210mm;height:112mm;background:linear-gradient(160deg,#2b5ea7,#1f4a8a)"></div>
<div style="position:absolute;left:18mm;top:20mm;color:#cfe0f5;font-size:9pt;letter-spacing:.2em;font-weight:600">MAINEXPERTS · ОТЧЁТ</div>
<div style="position:absolute;left:18mm;top:52mm;color:#fff;font-size:34pt;font-weight:300;line-height:1.15">Объём<br>SEO-страниц</div>
<div style="position:absolute;right:16mm;top:16mm;font-size:96pt;font-weight:300;color:rgba(255,255,255,.14);line-height:1">2026</div>
<div style="position:absolute;left:18mm;top:128mm;width:130mm;color:#22314a"><div style="font-size:14pt;color:#2b5ea7;line-height:1.35">Сколько страниц портала можно отдать в индекс уже сейчас и чего для этого не хватает</div>
<div style="font-size:9.5pt;color:#6f7f96;margin-top:6mm;line-height:1.6">Счёт по базе портала<br>Данные на 13.11.2026<br>Основа: отчёт разработки по заданию «Объём SEO-страниц»</div></div>
<div style="position:absolute;left:0;right:0;bottom:0;height:9mm;background:#8cc63f"></div></section>"""
    pages.append(cover)

    # --- 1. как читать
    cls_colors = {'K1': s['pal'][0], 'K2': s['pal'][1] if style == 'wave' else s['pal'][1], 'K3': s['pal'][2], 'K4': s['pal'][4], 'K5': s['pal'][5]}
    cls_text = [
        ('K1', 'В индекс', 'Страница готова: данных хватает, пороги выполнены. Можно отдавать поисковикам.', cls_colors['K1']),
        ('K2', 'После доработки', 'Данных достаточно, не хватает того, что можно добавить: срока подачи, FAQ, подборки, текста. Пока закрыта от индекса.', cls_colors['K2']),
        ('K3', 'Дубль родителя', 'Состав страницы совпадает со страницей выше (один вуз в городе, комбинация даёт тот же список). Отдельная страница не нужна.', cls_colors['K3']),
        ('K4', 'Оболочка', 'Объекты существуют, но данных меньше порога. Страница открыта людям, закрыта от индекса.', cls_colors['K4']),
        ('K5', 'Не создаётся', 'Нет объекта или нет программ. Адреса не будет.', cls_colors['K5']),
    ]
    k_html = ''.join(f'<div class="k"><div class="dot" style="background:{c}">{k}</div><div class="t"><b>{E(n)}.</b> {E(d)}</div></div>' for k, n, d, c in cls_text)
    inner = f"""<h1>Как читать этот отчёт</h1>
<p class="lead">Отчёт отвечает на один вопрос: сколько страниц портала поисковые системы могут увидеть и проиндексировать уже сейчас, а сколько нет и почему.</p>
<h2>Откуда цифры</h2>
<p>Разработка портала посчитала страницы по базе. Это <b>локальная копия для предпросмотра, не рабочая база</b>: в ней программы есть у 23 стран и их 390 467, а в матрице доступа команды указана другая база (81 страна, 848 942 программы). Поэтому цифры ниже показывают структуру проблемы, но не итоговый объём. На рабочей базе тот же счёт нужно повторить.</p>
<h2>Что значит «возможная страница»</h2>
<p>Сочетание, у которого может быть собственный адрес: например, «направление × страна» или «университет». Из всех возможных страниц каждая попадает ровно в один из пяти классов:</p>
{k_html}
<h2>Как читать таблицы</h2>
<ul><li><b>Строки сверху на цветном фоне</b> — типы, у которых есть страницы класса K1: они идут в индекс. Ниже — типы без K1, затем остальные.</li>
<li><b>Нижняя строка «Итого»</b> — сумма по каждому столбцу. Под таблицей — сумма всех классов и сверка с «Возможных».</li>
<li><b>Типы страниц</b> обозначены кодами T01, T02… (T01 — страна, T03 — вуз, T20 — «направление × страна», T43 — страница из выбранных фильтров). Расшифровка в первых столбцах каждой таблицы.</li>
<li><b>Сценарии порогов:</b> мягкий, базовый, жёсткий. Они определяют, сколько программ и вузов должно быть в комбинации, чтобы страница считалась достойной индекса. Главные выводы даны по базовому.</li>
<li><b>«—» и «не посчитано»</b> значит, что цифру взять неоткуда; причина указана рядом.</li></ul>
<p class="small">Отчёт не принимает решений об индексе: он показывает числа и причины. Выводы в конце помечены как наши.</p>"""
    pages.append(page_wrap(s, 1, 'Как читать', inner))

    # --- 2. итоги
    k1, k2 = tb[1], tb[2]
    top_k2 = sorted([(r[0] + ' ' + names[r[0]].replace('T43 страна + направление', 'страна·напр.').replace('+ уровень', '+ ур.').replace('+ язык', '+ яз.')[:30], num(r[4])) for r in cnt_b if num(r[4])], key=lambda x: -x[1])[:10]
    inner = f"""<h1>Итоги простыми словами</h1>
<p class="lead">Сейчас в индекс годятся <b>{fmt(k1)}</b> страниц. После доработки ещё <b>{fmt(k2)}</b>. Это доли процента от возможных {fmt(tb[0])}.</p>
<div class="cards">
<div class="card"><div class="big">{fmt(k1)}</div><div class="cap">идут в индекс (K1): вузы, колледжи, направления, сферы</div></div>
<div class="card"><div class="big">{fmt(k2)}</div><div class="cap">станут K1 после доработки (K2): нужны FAQ, подборки, тексты, срок подачи</div></div>
<div class="card"><div class="big">{fmt(tb[3])}</div><div class="cap">дубли родителя (K3): почти все — пары «отправление → программа» без своего текста</div></div></div>
<div style="display:flex;gap:6mm;align-items:center;margin-bottom:4mm">
<div>{donut([('K1', tb[1]), ('K2', tb[2]), ('K3', tb[3]), ('K4', tb[4]), ('K5', tb[5])], size=46, colors=[s['pal'][0], s['pal'][1], s['pal'][2], s['pal'][4], s['pal'][5]])}</div>
<div style="font-size:8.6pt;line-height:1.7"><b>Все возможные страницы по классам</b><br>
<i style="display:inline-block;width:3mm;height:3mm;background:{s['pal'][5]};vertical-align:-.4mm"></i> K5 не создаётся: {tb[5] * 100 / tb[0]:.1f} %<br>
<i style="display:inline-block;width:3mm;height:3mm;background:{s['pal'][2]};vertical-align:-.4mm"></i> K3 дубль родителя: {tb[3] * 100 / tb[0]:.1f} %<br>
<i style="display:inline-block;width:3mm;height:3mm;background:{s['pal'][4]};vertical-align:-.4mm"></i> K4 оболочка: {tb[4] * 100 / tb[0]:.1f} %<br>
<i style="display:inline-block;width:3mm;height:3mm;background:{s['pal'][1]};vertical-align:-.4mm"></i> K2 после доработки: {tb[2] * 100 / tb[0]:.2f} %<br>
<i style="display:inline-block;width:3mm;height:3mm;background:{s['pal'][0]};vertical-align:-.4mm"></i> K1 в индекс: {tb[1] * 100 / tb[0]:.4f} %</div></div>
<h2>Что можно открыть после доработки (K2 по типам, базовый сценарий)</h2>
{bars(top_k2, s['pal'][0], width=170, label_w=76)}
<h2>Почему в индекс идёт так мало</h2>
<ul><li>В базе нет ни одного блока FAQ и ни одной подборки: у страниц стран, городов, профессий и комбинаций не набирается минимум блоков.</li>
<li>Срок подачи есть в исходных данных, но не переносится в портал: страницы вузов уходят в K2 только из-за него (3 777 вузов и 1 326 колледжей).</li>
<li>Нет данных, которые отличают пару «из страны X в страну Y»: ни виз, ни признания документов. Есть только цена, а страницам нужно не меньше двух блоков.</li>
<li>Каталог сейчас закрыт целиком правилом «ждёт волны»: волн в таблице нет. Страницы K1 откроются, когда волну запустят.</li></ul>"""
    pages.append(page_wrap(s, 2, 'Итоги', inner))

    # --- 3. главная таблица (с группировкой)
    def scenario_page(n, title, lead, cnt, oth, tot_row, extra_note='', label=None):
        grp1 = [r for r in cnt if num(r[3]) > 0]
        grp2 = [r for r in cnt if num(r[3]) == 0 and num(r[4]) > 0]
        grp3 = [r for r in cnt if num(r[3]) == 0 and num(r[4]) == 0]
        body, cls = [], {}
        def add_group(label, rows, rowcls):
            if not rows: return
            body.append([label]); cls[len(body) - 1] = 'grp'
            for r in rows:
                body.append([r[0], r[1]] + [r[2 + i] for i in range(6)]); cls[len(body) - 1] = rowcls
        add_group('Идут в индекс сейчас (K1 > 0)', grp1, 'idx')
        add_group('Не идут в индекс сейчас, но могут после доработки (K2 > 0)', grp2, 'idx2')
        add_group('Остальные типы (нет K1 и K2)', grp3, '')
        header = ['Тип', 'Страница'] + COLS
        tot = ['Итого по таблице', ''] + tot_row
        tbl = table_html(header, body, cls_rows=cls, tot=['Итого по таблице'] + tot_row, dense=True)
        oth_html = ''
        if oth:
            oth_html = '<p class="small" style="margin-top:3mm"><b>Не входят в итог</b> (нет числа или это границы): ' + '; '.join(f'{E(r[0])} {E(r[1])}: {E(r[2])}' for r in oth) + '.</p>'
        ch = sum(tot_row[1:])
        sumbar = f'<div class="sumbar"><b>Сумма итого:</b> K1 + K2 + K3 + K4 + K5 = {fmt(tot_row[1])} + {fmt(tot_row[2])} + {fmt(tot_row[3])} + {fmt(tot_row[4])} + {fmt(tot_row[5])} = <b>{fmt(ch)}</b>. Возможных: <b>{fmt(tot_row[0])}</b>. ' + ('Сходится.' if ch == tot_row[0] else f'Расхождение {fmt(abs(ch - tot_row[0]))}.') + extra_note + '</div>'
        leg = f'<div class="legend"><span><i style="background:{s["hi"]}"></i>идёт в индекс (K1 &gt; 0)</span><span><i style="background:{s["hi2"]}"></i>может пойти после доработки (K2 &gt; 0)</span><span><i style="background:#fff;border:.2mm solid {s["line"]}"></i>остальные</span></div>'
        return page_wrap(s, n, title, f'<h1>{E(title)}</h1><p class="lead">{lead}</p>{leg}{fit(tbl + oth_html)}{sumbar}', label=label)
    pages.append(scenario_page(3, 'Главная таблица', 'Базовый сценарий порогов: не меньше 3 программ и 2 вузов в комбинации. Сверху на цветном фоне типы, которые идут в индекс.', cnt_b, oth_b, tb))

    # --- 4. пояснения к строкам
    expl = [[r[0], r[1], r[-1]] for r in sc_base[1:] if not r[0].startswith('Итого') and r[-1]]
    inner = f"""<h1>Что стоит за строками таблицы</h1><p class="lead">Короткое пояснение к каждому типу страницы: из чего сложились классы.</p>""" + fit(table_html(['Тип', 'Страница', 'Как разложено'], expl, left_cols=3, dense=True))
    pages.append(page_wrap(s, 3, 'Главная таблица', inner, label='3.1'))

    # --- 5. сценарии
    rows = []
    soft = {r[0]: r for r in cnt_s}; hard = {r[0]: r for r in cnt_h}
    for r in cnt_b:
        a, b = soft[r[0]], hard[r[0]]
        if any(num(x[i]) for x in (a, r, b) for i in (3, 4)):
            rows.append([r[0], r[1], a[3], r[3], b[3], a[4], r[4], b[4]])
    tot_sc = ['Итого по таблице', ts[1], tb[1], th_[1], ts[2], tb[2], th_[2]]
    tbl = table_html(['Тип', 'Страница', 'K1 мягк.', 'K1 баз.', 'K1 жёстк.', 'K2 мягк.', 'K2 баз.', 'K2 жёстк.'], rows, tot=tot_sc)
    sc_rows = [r for r in sc_tot[1:]]
    tbl2 = table_html(['Сценарий'] + COLS[1:], [[r[0]] + r[1:] for r in sc_rows], left_cols=1, code_col=False)
    inner = f"""<h1>Что меняют пороги</h1><p class="lead">Три сценария: <b>мягкий</b> (2 программы и 2 вуза), <b>базовый</b> (3 и 2), <b>жёсткий</b> (5 и 3). Показаны только типы, где K1 или K2 не нулевые.</p>{fit(tbl)}
<h2 style="margin-top:4mm">Итоги по всем классам</h2>{tbl2}
<div class="sumbar"><b>Вывод:</b> от мягкого к жёсткому K2 падает с {fmt(ts[2])} до {fmt(th_[2])} (минус {100 - th_[2] * 100 // ts[2]} %), K1 почти не меняется: {fmt(ts[1])}, {fmt(tb[1])}, {fmt(th_[1])}. Порог режет страницы-комбинации, но не вузы и направления.</div>"""
    pages.append(page_wrap(s, 4, 'Сценарии', inner))

    # --- 6. год набора
    ytab, fact = year_tabs[0], year_tabs[1]
    yt_total = sum(num(r[1]) for r in ytab[1:])
    inner = f"""<h1>Год набора и редакционные блоки</h1>
<p class="lead">Страницы с годом (2027 и позже) возможны только там, где у программ есть даты. Даты есть только у программ; календарь страны и сроки вуза в портал не переносятся.</p>
<h2>Комбинации с датированными программами (год ≥ 2027)</h2>
{fit(table_html(['Набор', 'Комбинаций'], ytab[1:], left_cols=1, code_col=False, tot=['Итого по таблице', yt_total]))}
<div class="sumbar"><b>Сумма итого:</b> {fmt(yt_total)} комбинаций с годом. В главную таблицу они не входят: страница с годом — вариант страницы без года.</div>
<h2 style="margin-top:4mm">Сколько редакционных блоков надо написать (по одному на значение фасета)</h2>
{table_html(['Фасет', 'Значений'], [[r[0], r[1]] for r in fact[1:] if not r[0].startswith('итого')], left_cols=1, code_col=False, tot=['Итого', 450])}
<p class="small" style="margin-top:2mm">Для страниц «отправление → страна, город, вуз, программа» тексты сейчас не нужны: они упираются в данные, а не в тексты.</p>"""
    pages.append(page_wrap(s, 5, 'Год набора', inner))

    # --- 7. причины K2
    detail = reasons[0][1:]
    cols = ['срок подачи', 'FAQ', 'подборка', 'текст', 'блоки по фасетам']
    piv, order = {}, []
    for r in detail:
        t, why, n_, only = r[0], r[1], num(r[2]), num(r[3])
        if n_ is None: continue
        if t not in piv: piv[t] = dict(zip(cols, [0] * 5)) | {'only': 0}; order.append(t)
        key = 'срок подачи' if why.startswith('срок подачи') else 'FAQ' if why.startswith('FAQ') else 'подборка' if why.startswith('подборка') else 'текст' if why.startswith('текст') else 'блоки по фасетам' if why.startswith('редакц') else None
        if key: piv[t][key] += n_
        piv[t]['only'] += only or 0
    body = [[t, names.get(t, '')] + [piv[t][c] for c in cols] + [piv[t]['only']] for t in order]
    colsum = [sum(b[2 + i] for b in body) for i in range(6)]
    inner = f"""<h1>Почему страницы остаются в K2</h1>
<p class="lead">У каждой страницы класса K2 данных достаточно, но не хватает одного или нескольких элементов. В таблице: сколько страниц не имеют каждого из них. Одна страница может не иметь сразу нескольких.</p>
{fit(table_html(['Тип', 'Страница'] + [c.capitalize() for c in cols] + ['Только эта причина'], body, tot=['Итого по таблице'] + colsum))}
<div class="sumbar"><b>Как читать «Только эта причина»:</b> страницы, которым до K1 не хватает ровно одного элемента. Таких всего {fmt(colsum[5])}: это вузы и колледжи без срока подачи (5 103) и страницы «T43» без редакционных блоков (9 845). У остальных типов нет ни FAQ, ни подборок одновременно, поэтому одной причины недостаточно.</div>
<p class="small" style="margin-top:2mm">Для T20…T26 также «не посчитано» число страниц, у которых нет 8 уникальных фактов: автотеста нет.</p>"""
    pages.append(page_wrap(s, 6, 'Причины', inner))

    # --- 8. чувствительность
    s_head, s_body = sens[0], sens[1:]
    s_tot = ['Итого по таблице'] + [sum(num(r[i]) for r in s_body) for i in range(1, 6)]
    inner = f"""<h1>Как порог влияет на число страниц</h1>
<p class="lead">Сколько страниц проходит порог при разных значениях «минимум программ в комбинации» (вузов не меньше двух). Помогает увидеть, где порог «ломает» объём.</p>
{fit(table_html(['Тип страницы'] + s_head[1:], s_body, left_cols=1, code_col=False, tot=s_tot))}
<div class="sumbar"><b>Вывод:</b> сильнее всего порог режет «направление × город» (T21): с 25 768 страниц при пороге 1–2 до 3 132 при пороге 10, в 8 раз. «Уровень × страна» и «профессия × страна» почти не меняются: у них комбинации крупные.</div>
<p class="small" style="margin-top:2mm">Строки T43 — справочные: они показывают, как порог действует на фасетные наборы.</p>"""
    pages.append(page_wrap(s, 7, 'Чувствительность', inner))

    # --- 9. происхождение × назначение
    o_tab, o_top = origin[0], origin[1]
    o_body = [[r[0], r[1], r[2], r[3], r[4], r[5], r[6]] for r in o_tab[1:]]
    inner = f"""<h1>Страница «из страны X в страну Y»</h1>
<p class="lead">Такая страница интересна, только если у пары есть собственные данные: виза, цена под гражданство, признание документов. В базе нашлась только <b>цена</b>, поэтому больше одного блока у пары не бывает, а нужно не меньше двух.</p>
{fit(table_html(['Уровень назначения', 'Возможных', 'Создаётся (200)', '0 блоков', '1 блок', '≥ 2 блока', 'Класс'], [[r[0]] + r[1:6] + [r[6]] for r in o_body if not r[1] == '0'], left_cols=1, code_col=False, tot=None))}
<div class="sumbar"><b>Пар «страна → страна» с двумя блоками данных: 0.</b> Стран отправления с данными: 36 (9 рынков портала и 27 стран ЕС). Виз и признания документов нет ни в портале, ни в доступных таблицах источника. Городов отправления нет вообще: страницы «из города» не создаются.</div>
<h2 style="margin-top:4mm">Страны отправления с наибольшим числом пар с данными</h2>
{table_html(['Страна', 'Стран назначения с данными', 'Блоков всего'], o_top[1:], left_cols=1, code_col=False)}
<p class="small" style="margin-top:2mm">Данных о спросе по странам отправления нет, поэтому порог «сколько стран отправления индексировать» применить не к чему.</p>"""
    pages.append(page_wrap(s, 8, 'Происхождение × назначение', inner))

    # --- 10. слепые зоны
    b1 = [r for r in blind61[1:]]
    def nz(r, i): return num(r[i]) or 0
    b1_tot = ['Итого по таблице', sum(nz(r, 1) for r in b1), sum(nz(r, 2) for r in b1), sum(nz(r, 3) for r in b1), sum(nz(r, 4) for r in b1)]
    b2 = blind62[1:]
    b2_tot = ['Итого по таблице', sum(nz(r, 1) for r in b2), '']
    inner = f"""<h1>Что мешает попасть в индекс</h1>
<h2>Страницы K2: чего не хватает</h2>
<p class="small">Сколько страниц K2 не имеют срока подачи, цены, текста от 300 знаков. «—» значит, что элемент типу не нужен.</p>
{table_html(['Тип', 'K2', 'Без срока подачи', 'Без цены', 'Без текста'], b1, left_cols=1, code_col=False, tot=b1_tot)}
<h2 style="margin-top:4mm">Дубли родителя (K3): чему дублируют</h2>
{table_html(['Тип', 'K3', 'Чему дублирует'], b2, left_cols=1, code_col=False, tot=b2_tot)}
<div class="sumbar"><b>Главное:</b> срок подачи есть в источнике, но не в портале. Календарь страны с будущими сроками у 7 стран (сейчас блок есть у 4), сроки вузов у 668 вузов в 12 странах. Перенос поднял бы K1 в первую очередь у вузов и колледжей.</div>"""
    pages.append(page_wrap(s, 9, 'Слепые зоны', inner))

    # --- 11. что уже есть
    cn = consist[1:]
    inner = f"""<h1>Что в портале уже есть сейчас</h1>
<div class="cards two">
<div class="card"><h3>Выдача и каталог</h3><div class="cap" style="font-size:8.6pt;color:{s['ink']}">«Подобрать» (<code>/find</code>) отдаёт <b>noindex, follow</b> и canonical на себя без параметров. Списки каталога с фильтрами — noindex. Каталог целиком сейчас закрыт правилом «ждёт волны»: волн нет.</div></div>
<div class="card"><h3>Sitemap</h3><div class="cap" style="font-size:8.6pt;color:{s['ink']}">3 файла, 25 служебных адресов (12 en и 13 ru). Страниц каталога нет: стран, вузов, программ в sitemap не существует.</div></div></div>
<h2>Языки</h2>{table_html(['Язык', 'Включён', 'Индексируется', 'Строк темы', 'Названия сущностей'], locales[1:], left_cols=2, code_col=False)}
<p class="small" style="margin-top:2mm">Падежей для русских заголовков в базе нет: поля «в Германии», «из Казахстана» не заведены.</p>
<h2 style="margin-top:3mm">Согласованность чисел</h2>
{table_html(['Уровень', 'Всего', 'Совпадает', 'Расходится', 'Сумма на страницах', 'Сумма в индексе'], cn, left_cols=1, code_col=False)}
<div class="sumbar"><b>Вывод:</b> число программ на странице и число в выдаче считаются разными путями: на страницах {fmt(478372)}, в выдаче {fmt(390467)}. Заметнее всего у Китая (45 254 против 308) и Казахстана (8 520 против 72). Посетитель увидит одно число на странице и другое после нажатия «Найти».</div>
<h2 style="margin-top:3mm">Защита выдачи от перебора</h2>
<ul><li>Лимит на адрес: 120 страниц, 600 чтений и 60 изменений за 60 секунд; сверх лимита ответ 429.</li>
<li>Глубина выдачи не больше 1 000 записей, страница до 100.</li>
<li>Капчи и проверки ботов нет. Распределённый перебор не остановить; при переполнении таблицы клиентов лимит открывается, а не закрывается.</li></ul>"""
    pages.append(page_wrap(s, 10, 'Что уже есть', inner))

    # --- 12. не найдено + сверка с матрицей
    mc = matrix_cmp[1:]
    inner = f"""<h1>Чего нет и чем это сверено</h1>
<h2>Не найдено в данных</h2>
<ul><li><b>Виза для гражданства × страна назначения</b> — нет ни в портале, ни в таблицах источника.</li>
<li><b>Цена под гражданство</b> — есть только аудитории «международные», «местные», «местные вне штата», «ЕС».</li>
<li><b>Признание документов, подтверждение средств</b> — нет.</li>
<li><b>Спрос по странам отправления и по формам обучения</b> — нет.</li>
<li><b>Города отправления</b> (визовые центры, консульства, перелёты) — нет.</li>
<li><b>Геообъекты</b> (достопримечательности, районы, регионы) — нет; страницы T50–T53 = 0.</li>
<li><b>Олимпиады, FAQ, подборки, статьи</b> — таблица пуста.</li>
<li><b>Метод близости для сравнений</b> — не реализован.</li>
<li><b>Поля падежей и короткие имена</b> — полей нет; короткое имя есть у 171 вуза.</li></ul>
<h2>Сверка с матрицей доступа</h2>
<p class="small">Матрица построена на другой базе. Столбец «Портал, локально» — что нашла разработка.</p>
{fit(table_html(['Параметр', 'Матрица', 'Портал, локально', 'Источник'], mc, left_cols=4, code_col=False))}"""
    pages.append(page_wrap(s, 11, 'Не найдено', inner))

    # --- 13. выводы
    inner = f"""<h1>Выводы и что делать дальше</h1>
<p class="lead">Это наши выводы по отчёту (не часть исходного счёта). Числа получены на локальной копии: перед решениями их нужно перепроверить на рабочей базе.</p>
<div class="cards two">
<div class="card"><h3>1. Открыть то, что готово</h3><div class="cap" style="font-size:8.6pt;color:{s['ink']}">{fmt(tb[1])} страниц (вузы, колледжи, направления, сферы) уже проходят пороги; нужна только волна, открывающая каталог.</div></div>
<div class="card"><h3>2. Перенести срок подачи</h3><div class="cap" style="font-size:8.6pt;color:{s['ink']}">Календарь стран и сроки вузов лежат в источнике. Это переводит 5 103 вуза и колледжа из K2 в K1 без работы редакции.</div></div>
<div class="card"><h3>3. Завести FAQ и подборки</h3><div class="cap" style="font-size:8.6pt;color:{s['ink']}">Их нет совсем. Это главный блокер для стран, городов, профессий и комбинаций (около 40 тысяч страниц K2).</div></div>
<div class="card"><h3>4. Написать 450 блоков</h3><div class="cap" style="font-size:8.6pt;color:{s['ink']}">По одному на значение фасета (404 направления, 20 стран, 16 языков, 7 уровней, 3 года): это даёт 9 845 страниц T43.</div></div>
<div class="card"><h3>5. Собрать данные для пар «из X в Y»</h3><div class="cap" style="font-size:8.6pt;color:{s['ink']}">Виза и цена под гражданство. Без них пара не набирает двух блоков, а это десятки миллионов адресов.</div></div>
<div class="card"><h3>6. Сверить числа и защитить выдачу</h3><div class="cap" style="font-size:8.6pt;color:{s['ink']}">Число на странице и в выдаче считаются разными запросами; у выдачи нет проверки ботов.</div></div></div>
<h2>Ограничения отчёта</h2>
<ul><li>Счёт по локальной копии (23 страны), не по рабочей базе (81 страна по матрице).</li>
<li>Правило «текст от 300 знаков» и «8 уникальных фактов» без автотестов: по ним числа «не посчитано».</li>
<li>Спрос по запросам не измерялся: сколько страниц проиндексирует поисковик, покажут вебмастера после запуска.</li>
<li>Строки сравнения «A или B» (T40) — границы, не точные числа, и в итог не входят.</li></ul>
<p class="small">Исходный отчёт разработки: <code>docs/26-seo-volume-report.md</code>. Правила и типы страниц: <code>docs/22-seo-page-tree-tz.md</code>.</p>"""
    pages.append(page_wrap(s, 12, 'Выводы', inner))

    # --- приложения: мягкий и жёсткий
    oth_s = split_scenario(sc_soft)[1]; oth_h = split_scenario(sc_hard)[1]
    pages.append(scenario_page(3, 'Приложение A. Мягкий сценарий', 'Порог мягкий: не меньше 2 программ и 2 вузов в комбинации.', cnt_s, oth_s, ts, label='A'))
    pages.append(scenario_page(3, 'Приложение B. Жёсткий сценарий', 'Порог жёсткий: не меньше 5 программ и 3 вузов в комбинации.', cnt_h, oth_h, th_, label='B'))

    # номера страниц в подвале: вместо номера раздела ставим сквозной
    body = ''.join(pages)
    idx = [0]
    def repl(m):
        idx[0] += 1
        return f'<span class="pn">{idx[0] + 1}</span>'
    body = re.sub(r'<span class="pn">[^<]*</span>', repl, body)
    script = """<script>
window.addEventListener('load', () => {
  document.querySelectorAll('.fitbox').forEach(box => {
    const f = box.querySelector('.fit'); f.style.zoom = 1;
    const bw = box.clientWidth, bh = box.clientHeight;
    const w = Math.max(f.scrollWidth, f.offsetWidth), h = f.scrollHeight;
    const k = Math.min(1, bw / w, bh / h);
    if (k < 1) { f.style.zoom = (k * 0.995).toFixed(4); f.dataset.zoom = k.toFixed(2); }
  });
  window.__ready = true;
});
</script>"""
    return f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Объём SEO-страниц</title><style>{css(s)}</style></head><body>{body}{script}</body></html>'

def main():
    style = sys.argv[1] if len(sys.argv) > 1 else 'corp'
    out = sys.argv[2] if len(sys.argv) > 2 else f'docs/26-seo-volume-report-{style}.pdf'
    htm = build(style)
    tmp = os.path.join(tempfile.gettempdir(), f'seo_report_{style}.html')
    open(tmp, 'w', encoding='utf-8').write(htm)
    import subprocess, json
    js = os.path.join(tempfile.gettempdir(), 'seo_report_render.js')
    open(js, 'w', encoding='utf-8').write("""
const { chromium } = require('playwright');
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + html); await p.waitForFunction('window.__ready === true');
  const z = await p.evaluate(() => [...document.querySelectorAll('.fit')].map(f => f.dataset.zoom || '1'));
  await p.pdf({ path: out, preferCSSPageSize: true, printBackground: true });
  await b.close(); console.log('PDF', out, 'масштабы таблиц:', z.join(' '));
})();
""")
    subprocess.run(['node', js, tmp, os.path.abspath(out)], check=True)

if __name__ == '__main__':
    main()
