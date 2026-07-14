#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка PLAYBOOK «Система получения отзывов MainExperts» — Глава 1.
Дизайн-грейд: A4, поля 20 мм, DejaVu Sans, палитра бренда, рисованные схемы (inline SVG),
таблицы с цветной шапкой и зеброй, callout-блоки, чек-листы, тайм-лайны.
Рендер: WeasyPrint (нативная постраничная модель, номера страниц, колонтитулы).

Выход: vault/40-reports/playbook-otzyvy/01_Философия_системы_получения_отзывов_MainExperts.pdf
"""

import os
from weasyprint import HTML

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "vault", "40-reports", "playbook-otzyvy")
OUT_DIR = os.path.abspath(OUT_DIR)
PDF_NAME = "01_Философия_системы_получения_отзывов_MainExperts.pdf"
HTML_DEBUG = os.path.join(OUT_DIR, "ch01-source.html")

# ── Палитра бренда ──────────────────────────────────────────────────────────
PRIMARY   = "#1D4ED8"   # основной
SECONDARY = "#0F172A"   # вторичный (текст/тёмный)
ACCENT    = "#10B981"   # акцент (успех)
WARNING   = "#F59E0B"   # предупреждение
ERROR     = "#DC2626"   # ошибка/риск
INK       = "#1E293B"
MUTED     = "#64748B"
LINE      = "#E2E8F0"
BG_SOFT   = "#F8FAFC"

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
CSS = f"""
:root {{
  --primary:{PRIMARY}; --secondary:{SECONDARY}; --accent:{ACCENT};
  --warning:{WARNING}; --error:{ERROR}; --ink:{INK}; --muted:{MUTED};
  --line:{LINE}; --bg:{BG_SOFT};
}}

/* ---- Постраничная модель ---- */
@page {{
  size: A4;
  margin: 20mm 20mm 20mm 20mm;
  @bottom-left  {{ content: "PLAYBOOK · Система получения отзывов MainExperts";
                  font-family:'DejaVu Sans'; font-size:7.5pt; color:{MUTED}; }}
  @bottom-right {{ content: counter(page);
                  font-family:'DejaVu Sans'; font-size:8.5pt; font-weight:bold; color:{SECONDARY}; }}
  @top-right    {{ content: string(chaptitle);
                  font-family:'DejaVu Sans'; font-size:7.5pt; color:{MUTED}; }}
}}
@page cover  {{ margin:0;
  @bottom-left{{content:none}} @bottom-right{{content:none}} @top-right{{content:none}} }}
@page chapter {{ @top-right{{content:none}} @bottom-left{{content:none}} }}

/* ---- База ---- */
* {{ box-sizing:border-box; }}
html {{ font-family:'DejaVu Sans', sans-serif; }}
body {{
  margin:0; color:var(--ink); font-size:11.5pt; line-height:1.4;
  -weasy-hyphens:none;
}}
p {{ margin:0 0 7pt 0; text-align:justify; }}
strong {{ color:var(--secondary); }}
h1,h2,h3 {{ font-weight:bold; color:var(--secondary); margin:0; line-height:1.2; }}
h1 {{ font-size:26pt; }}
h2 {{ font-size:20pt; }}
h3 {{ font-size:16pt; }}
ul,ol {{ margin:0 0 8pt 0; padding-left:16pt; }}
li {{ margin:0 0 4pt 0; }}
a {{ color:var(--primary); text-decoration:none; }}
.small {{ font-size:9pt; color:var(--muted); }}

/* ---- Обложка ---- */
.cover {{ page:cover; height:297mm; position:relative; color:#fff;
  background:
    radial-gradient(1200px 500px at 78% -8%, rgba(16,185,129,.35), transparent 60%),
    linear-gradient(150deg, {SECONDARY} 0%, #16265c 46%, {PRIMARY} 100%);
  overflow:hidden; }}
.cover .frame {{ position:absolute; inset:14mm; border:1px solid rgba(255,255,255,.22); }}
.cover .inner {{ position:absolute; inset:14mm; padding:16mm 16mm; display:block; }}
.cover .eyebrow {{ letter-spacing:.42em; font-size:11pt; color:rgba(255,255,255,.72);
  text-transform:uppercase; margin-bottom:8mm; }}
.cover .kicker {{ display:inline-block; font-size:9.5pt; letter-spacing:.28em;
  text-transform:uppercase; color:{ACCENT}; border:1px solid rgba(16,185,129,.55);
  padding:3pt 10pt; border-radius:20pt; margin-bottom:10mm; }}
.cover h1 {{ color:#fff; font-size:41pt; line-height:1.08; margin:0 0 6mm 0; letter-spacing:-.5pt; }}
.cover .sub {{ font-size:14pt; color:rgba(255,255,255,.86); max-width:150mm; line-height:1.45; }}
.cover .ver {{ position:absolute; left:32mm; bottom:46mm; font-size:12pt; color:#fff; }}
.cover .ver b {{ font-size:15pt; }}
.cover .meta {{ position:absolute; left:32mm; right:32mm; bottom:18mm;
  display:flex; justify-content:space-between; align-items:flex-end;
  font-size:8.5pt; color:rgba(255,255,255,.66);
  border-top:1px solid rgba(255,255,255,.2); padding-top:5mm; }}
.cover .wm {{ position:absolute; right:-40mm; top:120mm; font-size:190pt; font-weight:bold;
  color:rgba(255,255,255,.05); letter-spacing:-6pt; }}

/* ---- Заголовки элементов главы (плашка) ---- */
.eltag {{ display:inline-block; font-size:8.5pt; font-weight:bold; letter-spacing:.16em;
  text-transform:uppercase; color:#fff; background:var(--primary);
  padding:3.5pt 10pt; border-radius:4pt; margin-bottom:7pt; }}
.eltag.accent {{ background:var(--accent); }}
.eltag.dark {{ background:var(--secondary); }}
.eltag.warn {{ background:var(--warning); color:{SECONDARY}; }}
.eyebrow {{ font-size:8.5pt; letter-spacing:.24em; text-transform:uppercase;
  color:var(--primary); font-weight:bold; margin-bottom:4pt; }}

section {{ margin-bottom:14pt; }}
.newpage {{ break-before:page; }}
.keep {{ break-inside:avoid; break-after:avoid; }}
.goalbox, .checklist, .summary, .grow, .recs {{ break-inside:avoid; }}
h2 {{ margin-top:2pt; margin-bottom:8pt; padding-bottom:5pt;
  border-bottom:2.5pt solid var(--primary); break-after:avoid; }}
h3 {{ margin-top:10pt; margin-bottom:5pt; color:var(--primary); break-after:avoid; }}
.eltag {{ break-after:avoid; }}
.lead-in {{ break-after:avoid; }}

/* ---- Титул главы ---- */
.chapter-title {{ page:chapter; break-before:page; height:255mm; position:relative;
  display:flex; flex-direction:column; justify-content:center; }}
.chapter-title .no {{ font-size:15pt; letter-spacing:.4em; color:var(--primary);
  text-transform:uppercase; font-weight:bold; }}
.chapter-title .bar {{ width:64mm; height:5pt; background:var(--accent); margin:9pt 0 12pt; border-radius:3pt; }}
.chapter-title h1 {{ font-size:33pt; line-height:1.12; max-width:150mm; }}
.chapter-title .lead {{ font-size:13pt; color:var(--muted); max-width:140mm; margin-top:10pt; line-height:1.5; }}
.chapter-title .foot {{ position:absolute; bottom:0; left:0; right:0; font-size:8.5pt;
  color:var(--muted); border-top:1px solid var(--line); padding-top:6pt;
  display:flex; justify-content:space-between; }}

/* ---- Цель ---- */
.goalbox {{ background:linear-gradient(180deg,#fff, {BG_SOFT});
  border:1px solid var(--line); border-left:6pt solid var(--accent);
  border-radius:8pt; padding:12pt 15pt; }}
.goalbox .big {{ font-size:13.5pt; line-height:1.45; color:var(--secondary); }}

/* ---- Карточки понятий ---- */
.grid2 {{ display:table; width:100%; border-collapse:separate; border-spacing:9pt; margin:0 -9pt; }}
.grow {{ display:table-row; }}
.gcell {{ display:table-cell; width:50%; vertical-align:top; }}
.concept {{ border:1px solid var(--line); border-top:3pt solid var(--primary);
  border-radius:8pt; padding:10pt 12pt; background:#fff; height:100%; }}
.concept .term {{ font-size:11.5pt; font-weight:bold; color:var(--secondary); margin-bottom:3pt; }}
.concept .def {{ font-size:10pt; color:var(--ink); line-height:1.38; text-align:left; }}
.concept .tagline {{ display:inline-block; margin-top:5pt; font-size:8pt; letter-spacing:.06em;
  color:var(--primary); background:#EFF4FF; border-radius:12pt; padding:2pt 8pt; }}

/* ---- Схемы ---- */
figure {{ margin:11pt 0; break-inside:avoid; }}
.schema {{ border:1px solid var(--line); border-radius:10pt; background:#fff;
  padding:12pt 12pt 6pt; }}
.schema svg {{ width:100%; height:auto; display:block; }}
figcaption {{ font-size:8.7pt; color:var(--muted); margin-top:7pt; padding-top:6pt;
  border-top:1px dashed var(--line); }}
figcaption b {{ color:var(--primary); }}

/* ---- Таблицы ---- */
.tablewrap {{ border:1px solid var(--line); border-radius:9pt; overflow:hidden; margin:10pt 0; }}
table.data {{ width:100%; border-collapse:collapse; font-size:9.6pt; }}
table.data thead th {{ background:var(--primary); color:#fff; text-align:left;
  padding:7pt 9pt; font-size:9pt; letter-spacing:.02em; border-right:1px solid rgba(255,255,255,.16); }}
table.data thead th:last-child {{ border-right:none; }}
table.data td {{ padding:6.5pt 9pt; border-top:1px solid var(--line); vertical-align:top; line-height:1.34; }}
table.data tbody tr:nth-child(even) {{ background:{BG_SOFT}; }}
table.data td.k {{ font-weight:bold; color:var(--secondary); white-space:nowrap; }}
.pill {{ display:inline-block; font-size:8pt; font-weight:bold; padding:1.5pt 7pt; border-radius:10pt; }}
.pill.p1 {{ background:#FEF3C7; color:#92400E; }}
.pill.p2 {{ background:#DBEAFE; color:#1E40AF; }}
.pill.both {{ background:#D1FAE5; color:#065F46; }}

/* ---- Callout ---- */
.callout {{ display:table; width:100%; border-radius:8pt; padding:10pt 12pt; margin:10pt 0;
  border:1px solid; break-inside:avoid; }}
.callout .ic {{ display:table-cell; width:26pt; vertical-align:top; padding-right:9pt; }}
.callout .bd {{ display:table-cell; vertical-align:top; font-size:10pt; line-height:1.42; text-align:left; }}
.callout .hd {{ font-weight:bold; font-size:10.5pt; margin-bottom:2pt; }}
.c-imp  {{ background:#FFFBEB; border-color:{WARNING}; }}
.c-imp  .hd {{ color:#92400E; }}
.c-note {{ background:#EFF4FF; border-color:{PRIMARY}; }}
.c-note .hd {{ color:{PRIMARY}; }}
.c-tip  {{ background:#ECFDF5; border-color:{ACCENT}; }}
.c-tip  .hd {{ color:#065F46; }}
.c-risk {{ background:#FEF2F2; border-color:{ERROR}; }}
.c-risk .hd {{ color:{ERROR}; }}

/* ---- Боковая заметка ---- */
.sidenote {{ float:right; width:44%; margin:0 0 8pt 12pt; background:{BG_SOFT};
  border:1px solid var(--line); border-left:4pt solid var(--secondary);
  border-radius:6pt; padding:9pt 11pt; font-size:9pt; line-height:1.4; text-align:left; }}
.sidenote .t {{ font-weight:bold; color:var(--secondary); font-size:9.2pt; margin-bottom:3pt;
  letter-spacing:.04em; }}

/* ---- Пример ---- */
.example {{ border:1px solid var(--line); border-radius:8pt; overflow:hidden; margin:9pt 0; break-inside:avoid; }}
.example .top {{ background:var(--secondary); color:#fff; padding:6pt 11pt; font-size:9.5pt; font-weight:bold; }}
.example .top .tag {{ float:right; font-size:8pt; font-weight:normal; opacity:.85; }}
.example .bdy {{ padding:9pt 11pt; font-size:9.8pt; line-height:1.42; }}
.example .bdy .step {{ margin-bottom:4pt; }}
.example .bef {{ color:{ERROR}; font-weight:bold; }}
.example .aft {{ color:#065F46; font-weight:bold; }}

/* ---- Рекомендации ---- */
.recs {{ display:table; width:100%; border-spacing:8pt; margin:0 -8pt; }}
.rec {{ display:table-cell; width:33.33%; vertical-align:top; background:#fff;
  border:1px solid var(--line); border-radius:8pt; padding:9pt 10pt; }}
.rec .n {{ display:inline-flex; width:20pt; height:20pt; align-items:center; justify-content:center;
  background:var(--primary); color:#fff; border-radius:50%; font-weight:bold; font-size:10pt; margin-bottom:5pt; }}
.rec .rt {{ font-weight:bold; font-size:10pt; color:var(--secondary); margin-bottom:3pt; }}
.rec .rd {{ font-size:9pt; color:var(--ink); line-height:1.36; text-align:left; }}

/* ---- Чек-лист ---- */
.checklist {{ border:1px solid var(--line); border-top:4pt solid var(--accent);
  border-radius:9pt; padding:11pt 13pt; background:#fff; }}
.checklist .ci {{ display:table; width:100%; margin-bottom:6pt; }}
.checklist .box {{ display:table-cell; width:20pt; vertical-align:top; padding-top:1pt; }}
.checklist .txt {{ display:table-cell; vertical-align:top; font-size:10pt; line-height:1.38; text-align:left; }}
.checklist .txt b {{ color:var(--secondary); }}

/* ---- Резюме ---- */
.summary {{ background:linear-gradient(160deg,{SECONDARY},#1e2f66); color:#fff;
  border-radius:10pt; padding:14pt 16pt; }}
.summary h3 {{ color:#fff; margin-top:0; }}
.summary ol {{ margin:6pt 0 0; padding-left:16pt; }}
.summary li {{ margin-bottom:5pt; font-size:10.3pt; line-height:1.4; color:rgba(255,255,255,.94); }}
.summary li b {{ color:{ACCENT}; }}

/* ---- Переход ---- */
.transition {{ display:table; width:100%; background:#EFF4FF; border:1px solid #BFD3FF;
  border-radius:10pt; padding:13pt 15pt; margin-top:12pt; }}
.transition .l {{ display:table-cell; vertical-align:middle; }}
.transition .r {{ display:table-cell; width:56pt; vertical-align:middle; text-align:right; }}
.transition .nx {{ font-size:8.5pt; letter-spacing:.2em; text-transform:uppercase;
  color:var(--primary); font-weight:bold; }}
.transition h3 {{ margin:3pt 0 4pt; color:var(--secondary); }}
.transition p {{ margin:0; font-size:10pt; color:var(--ink); text-align:left; }}

/* ---- Разделитель ---- */
.divider {{ display:flex; align-items:center; gap:9pt; margin:13pt 0; color:var(--line); }}
.divider::before,.divider::after {{ content:""; flex:1; height:1px; background:var(--line); }}
.divider .dot {{ width:7pt; height:7pt; background:var(--accent); transform:rotate(45deg); }}

.lead-in {{ font-size:11.5pt; color:var(--muted); line-height:1.5; margin-bottom:9pt; }}

/* ---- «О плейбуке» ---- */
.audience {{ display:table; width:100%; border-spacing:6pt; margin:6pt -6pt; }}
.audrow {{ display:table-row; }}
.aud {{ display:table-cell; width:33.33%; background:#fff; border:1px solid var(--line);
  border-radius:7pt; padding:7pt 9pt; font-size:9pt; vertical-align:middle; }}
.aud b {{ color:var(--secondary); }}
.toc2 {{ display:table; width:100%; border-spacing:9pt 0; margin:0 -9pt; }}
.toccol {{ display:table-cell; width:50%; vertical-align:top; }}
.toc {{ border:1px solid var(--line); border-radius:9pt; overflow:hidden; }}
.toc .row {{ display:table; width:100%; border-top:1px solid var(--line); }}
.toc .row:first-child {{ border-top:none; }}
.toc .num {{ display:table-cell; width:30pt; background:{BG_SOFT}; text-align:center;
  font-weight:bold; color:var(--primary); vertical-align:middle; padding:6pt 4pt; }}
.toc .lbl {{ display:table-cell; padding:6pt 9pt; font-size:9pt; vertical-align:middle; line-height:1.3; }}
.toc .lbl b {{ color:var(--secondary); }}
"""

# ══════════════════════════════════════════════════════════════════════════════
# Иконки (inline SVG, монохром)
# ══════════════════════════════════════════════════════════════════════════════
def icon(kind, color):
    paths = {
        "info": '<circle cx="12" cy="12" r="10" fill="none" stroke="{c}" stroke-width="2"/>'
                '<circle cx="12" cy="7.6" r="1.4" fill="{c}"/>'
                '<rect x="10.7" y="10.6" width="2.6" height="7" rx="1.3" fill="{c}"/>',
        "warn": '<path d="M12 3 L22 20 H2 Z" fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round"/>'
                '<rect x="10.8" y="9" width="2.4" height="6" rx="1.2" fill="{c}"/>'
                '<circle cx="12" cy="17.4" r="1.3" fill="{c}"/>',
        "check":'<circle cx="12" cy="12" r="10" fill="none" stroke="{c}" stroke-width="2"/>'
                '<path d="M7.5 12.5 L10.7 15.5 L16.5 8.6" fill="none" stroke="{c}" '
                'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>',
        "risk": '<path d="M12 2 L21 6 V12 C21 17 17 20.5 12 22 C7 20.5 3 17 3 12 V6 Z" '
                'fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round"/>'
                '<rect x="10.8" y="8" width="2.4" height="6" rx="1.2" fill="{c}"/>'
                '<circle cx="12" cy="16.4" r="1.2" fill="{c}"/>',
        "star": '<path d="M12 2.5 L14.9 8.6 L21.5 9.5 L16.7 14.1 L17.9 20.6 L12 17.5 '
                'L6.1 20.6 L7.3 14.1 L2.5 9.5 L9.1 8.6 Z" fill="{c}"/>',
    }
    return (f'<svg viewBox="0 0 24 24" width="20" height="20" '
            f'xmlns="http://www.w3.org/2000/svg">{paths[kind].format(c=color)}</svg>')

def checkbox():
    return ('<svg viewBox="0 0 24 24" width="15" height="15" xmlns="http://www.w3.org/2000/svg">'
            f'<rect x="2.5" y="2.5" width="19" height="19" rx="4" fill="#fff" '
            f'stroke="{PRIMARY}" stroke-width="2"/></svg>')

# ══════════════════════════════════════════════════════════════════════════════
# СХЕМА 1 — Путь сопровождения семьи (тайм-лайн из 3 фаз, 11 этапов)
# ══════════════════════════════════════════════════════════════════════════════
def schema_journey():
    phases = [
        ("Фаза 1 · Выбор пути", PRIMARY,
         ["Профориентация", "Диагностика способностей", "Выбор профессии"]),
        ("Фаза 2 · Поступление", "#4338CA",
         ["Выбор университета", "Обучение", "Доп. предметы", "Поступление"]),
        ("Фаза 3 · Переход в жизнь", ACCENT,
         ["Визовая поддержка", "Релокация", "Адаптация", "Первое место работы"]),
    ]
    W, gap = 254, 24
    xs = [15, 15 + W + gap, 15 + 2*(W + gap)]
    chip_h, chip_gap, head_h = 30, 8, 34
    maxchips = max(len(p[2]) for p in phases)
    box_h = head_h + 12 + maxchips*(chip_h+chip_gap)
    top = 8
    svg = [f'<svg viewBox="0 0 840 {top+box_h+96}" xmlns="http://www.w3.org/2000/svg" '
           f'font-family="DejaVu Sans">']
    # фазы
    for (title, color, chips), x in zip(phases, xs):
        svg.append(f'<rect x="{x}" y="{top}" width="{W}" height="{box_h}" rx="12" '
                   f'fill="#ffffff" stroke="{color}" stroke-width="1.6"/>')
        svg.append(f'<path d="M{x+12},{top} H{x+W-12} A12,12 0 0 1 {x+W},{top+12} '
                   f'V{top+head_h} H{x} V{top+12} A12,12 0 0 1 {x+12},{top} Z" fill="{color}"/>')
        svg.append(f'<text x="{x+W/2:.0f}" y="{top+22}" fill="#ffffff" font-size="12.5" '
                   f'font-weight="bold" text-anchor="middle">{title}</text>')
        cy = top + head_h + 12
        for ch in chips:
            svg.append(f'<rect x="{x+12}" y="{cy}" width="{W-24}" height="{chip_h}" rx="7" '
                       f'fill="{BG_SOFT}" stroke="{LINE}" stroke-width="1"/>')
            svg.append(f'<circle cx="{x+26}" cy="{cy+chip_h/2:.0f}" r="4" fill="{color}"/>')
            svg.append(f'<text x="{x+40}" y="{cy+chip_h/2+4:.0f}" fill="{INK}" '
                       f'font-size="11.5">{ch}</text>')
            cy += chip_h + chip_gap
    # стрелки между фазами
    for i in range(2):
        ax = xs[i] + W + 4
        ay = top + box_h/2
        svg.append(f'<path d="M{ax},{ay-8:.0f} L{ax+18},{ay:.0f} L{ax},{ay+8:.0f} Z" '
                   f'fill="{MUTED}"/>')
    # лента отзывов
    ry = top + box_h + 30
    rx0, rx1 = 15, 825
    svg.append(f'<rect x="{rx0}" y="{ry}" width="{rx1-rx0}" height="46" rx="12" '
               f'fill="#ECFDF5" stroke="{ACCENT}" stroke-width="1.6"/>')
    svg.append(f'<circle cx="{rx0+26}" cy="{ry+23}" r="11" fill="{ACCENT}"/>')
    svg.append(f'<path d="M{rx0+21},{ry+23} l4,4 l7,-8" stroke="#fff" stroke-width="2.4" '
               f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    svg.append(f'<text x="{rx0+46}" y="{ry+21}" fill="#065F46" font-size="12" font-weight="bold">'
               f'Поток свидетельств: отзыв рождается на каждом этапе пути,</text>')
    svg.append(f'<text x="{rx0+46}" y="{ry+37}" fill="#065F46" font-size="12">'
               f'а не только в его финале.</text>')
    # пунктиры от фаз к ленте
    for x in xs:
        cx = x + W/2
        svg.append(f'<path d="M{cx:.0f},{top+box_h} V{ry}" stroke="{ACCENT}" '
                   f'stroke-width="1.4" stroke-dasharray="3 3"/>')
        svg.append(f'<circle cx="{cx:.0f}" cy="{ry}" r="3.5" fill="{ACCENT}"/>')
    svg.append('</svg>')
    return "".join(svg)

# ══════════════════════════════════════════════════════════════════════════════
# СХЕМА 2 — Два клиента, два голоса (дерево)
# ══════════════════════════════════════════════════════════════════════════════
def schema_two_clients():
    svg = ['<svg viewBox="0 0 840 278" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    # платформа сверху
    px, pw = 300, 240
    svg.append(f'<rect x="{px}" y="8" width="{pw}" height="46" rx="10" fill="{SECONDARY}"/>')
    svg.append(f'<text x="{px+pw/2:.0f}" y="30" fill="#fff" font-size="12.5" font-weight="bold" '
               f'text-anchor="middle">MainExperts</text>')
    svg.append(f'<text x="{px+pw/2:.0f}" y="46" fill="rgba(255,255,255,.8)" font-size="10" '
               f'text-anchor="middle">платформа сопровождения</text>')
    # ветви
    svg.append(f'<path d="M{px+pw/2:.0f},54 C{px+pw/2:.0f},82 210,72 210,100" fill="none" '
               f'stroke="{PRIMARY}" stroke-width="2"/>')
    svg.append(f'<path d="M{px+pw/2:.0f},54 C{px+pw/2:.0f},82 630,72 630,100" fill="none" '
               f'stroke="{ACCENT}" stroke-width="2"/>')
    cols = [
        (60, PRIMARY, "СЕМЬИ", "родители и подросток",
         "Свидетельствуют о результате", "«было → стало»: тревога снята,\nпуть ребёнка виден",
         "Публичное соц. доказательство\nдля новых семей"),
        (480, ACCENT, "ЭКСПЕРТЫ", "те, кто ведёт сопровождение",
         "Свидетельствуют о процессе", "качество платформы\nи методики в работе",
         "Калибровка сети · доказательство\nкомпетенции эксперта"),
    ]
    for x, color, head, sub, s1, s2, s3 in cols:
        w = 300
        # шапка ветви
        svg.append(f'<rect x="{x}" y="100" width="{w}" height="42" rx="9" fill="{color}"/>')
        svg.append(f'<text x="{x+w/2:.0f}" y="120" fill="#fff" font-size="12" font-weight="bold" '
                   f'text-anchor="middle">{head}</text>')
        svg.append(f'<text x="{x+w/2:.0f}" y="135" fill="rgba(255,255,255,.9)" font-size="9.5" '
                   f'text-anchor="middle">{sub}</text>')
        # блок 1
        svg.append(f'<rect x="{x}" y="152" width="{w}" height="56" rx="8" fill="#fff" '
                   f'stroke="{color}" stroke-width="1.3"/>')
        svg.append(f'<text x="{x+14}" y="170" fill="{SECONDARY}" font-size="11" '
                   f'font-weight="bold">{s1}</text>')
        for i, ln in enumerate(s2.split("\n")):
            svg.append(f'<text x="{x+14}" y="{185+i*13}" fill="{INK}" font-size="9.5">{ln}</text>')
        # блок 2 (где работает)
        svg.append(f'<rect x="{x}" y="216" width="{w}" height="52" rx="8" fill="{BG_SOFT}" '
                   f'stroke="{LINE}" stroke-width="1"/>')
        svg.append(f'<text x="{x+14}" y="233" fill="{MUTED}" font-size="8.5" '
                   f'font-weight="bold" letter-spacing="1">ГДЕ РАБОТАЕТ</text>')
        for i, ln in enumerate(s3.split("\n")):
            svg.append(f'<text x="{x+14}" y="{247+i*13}" fill="{INK}" font-size="9.5">{ln}</text>')
    svg.append('</svg>')
    return "".join(svg)

# ══════════════════════════════════════════════════════════════════════════════
# СХЕМА 3 — Петля ценности отзыва (цикл + ветка знания)
# ══════════════════════════════════════════════════════════════════════════════
def schema_value_loop():
    svg = ['<svg viewBox="0 0 840 300" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    nodes = [
        ("Впечатление\nна этапе", PRIMARY),
        ("Сбор\nсвидетельства", PRIMARY),
        ("Библиотека\nотзывов — актив", ACCENT),
        ("Снижение риска\nу новой семьи", PRIMARY),
        ("Рост доверия\nи сопровождения", SECONDARY),
    ]
    bw, bh = 148, 62
    xs = [12, 12+168, 12+2*168, 12+3*168, 12+4*168]
    y = 96
    for (label, color), x in zip(nodes, xs):
        svg.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="10" fill="#fff" '
                   f'stroke="{color}" stroke-width="1.8"/>')
        svg.append(f'<rect x="{x}" y="{y}" width="5" height="{bh}" rx="2.5" fill="{color}"/>')
        for i, ln in enumerate(label.split("\n")):
            svg.append(f'<text x="{x+bw/2+3:.0f}" y="{y+bh/2-4+i*15:.0f}" fill="{SECONDARY}" '
                       f'font-size="11" font-weight="bold" text-anchor="middle">{ln}</text>')
    # стрелки вперёд
    for i in range(4):
        ax = xs[i]+bw
        svg.append(f'<path d="M{ax},{y+bh/2:.0f} H{xs[i+1]-4}" stroke="{MUTED}" stroke-width="1.8"/>')
        svg.append(f'<path d="M{xs[i+1]-4},{y+bh/2-5:.0f} l6,5 l-6,5 Z" fill="{MUTED}"/>')
    # возвратная дуга сверху 5→1
    x5c = xs[4]+bw/2
    x1c = xs[0]+bw/2
    svg.append(f'<path d="M{x5c:.0f},{y} C{x5c:.0f},20 {x1c:.0f},20 {x1c:.0f},{y}" '
               f'fill="none" stroke="{PRIMARY}" stroke-width="1.8" stroke-dasharray="6 4"/>')
    svg.append(f'<path d="M{x1c-5:.0f},{y-4} l5,6 l5,-6 Z" fill="{PRIMARY}"/>')
    svg.append(f'<text x="420" y="17" fill="{PRIMARY}" font-size="10" font-weight="bold" '
               f'text-anchor="middle">накопительный эффект — цикл повторяется</text>')
    # ветка знания вниз от узла 3
    x3c = xs[2]+bw/2
    svg.append(f'<path d="M{x3c:.0f},{y+bh} V{y+bh+30}" stroke="{ACCENT}" stroke-width="1.8"/>')
    svg.append(f'<path d="M{x3c-5:.0f},{y+bh+30} l5,6 l5,-6 Z" fill="{ACCENT}"/>')
    kb_w = 360
    kbx = x3c - kb_w/2
    svg.append(f'<rect x="{kbx:.0f}" y="{y+bh+36}" width="{kb_w}" height="46" rx="10" '
               f'fill="#ECFDF5" stroke="{ACCENT}" stroke-width="1.5"/>')
    svg.append(f'<text x="{x3c:.0f}" y="{y+bh+58}" fill="#065F46" font-size="11" '
               f'font-weight="bold" text-anchor="middle">Знание → улучшение продукта и сопровождения</text>')
    svg.append(f'<text x="{x3c:.0f}" y="{y+bh+73}" fill="#065F46" font-size="9.5" '
               f'text-anchor="middle">отзыв замыкает петлю управления ценностью (V4.1)</text>')
    svg.append('</svg>')
    return "".join(svg)

# ══════════════════════════════════════════════════════════════════════════════
# СХЕМА 4 — Два потока — две механики отзыва (разделённая панель)
# ══════════════════════════════════════════════════════════════════════════════
def schema_two_streams():
    svg = ['<svg viewBox="0 0 840 214" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">']
    panels = [
        (15, WARNING, "#FFFBEB", "#92400E", "Поток 1 · Founder Premium",
         "Личные продажи по рекомендации (HNW / UHNW)",
         ["Отзыв = приватная рекомендация в узком кругу",
          "Валюта — доверие и репутация, не контент",
          "Не публикуется, не выносится в воронку"]),
        (465, PRIMARY, "#EFF4FF", "#1E40AF", "Поток 2 · Platform",
         "Воронка самообслуживания (freemium → апсейл)",
         ["Отзыв = публичное социальное доказательство",
          "Работает на лендинге, в рассылке, в отчёте",
          "Снижает стоимость лида и повышает конверсию"]),
    ]
    for x, color, bg, tc, title, sub, items in panels:
        w = 360
        svg.append(f'<rect x="{x}" y="8" width="{w}" height="198" rx="12" fill="{bg}" '
                   f'stroke="{color}" stroke-width="1.8"/>')
        svg.append(f'<rect x="{x}" y="8" width="{w}" height="6" rx="3" fill="{color}"/>')
        svg.append(f'<text x="{x+18}" y="42" fill="{tc}" font-size="13" font-weight="bold">{title}</text>')
        svg.append(f'<text x="{x+18}" y="60" fill="{INK}" font-size="9.5">{sub}</text>')
        yy = 86
        for it in items:
            svg.append(f'<circle cx="{x+22}" cy="{yy-4}" r="3.2" fill="{color}"/>')
            svg.append(f'<text x="{x+34}" y="{yy}" fill="{INK}" font-size="10.3">{it}</text>')
            yy += 26
    # центральный разделитель
    svg.append(f'<line x1="420" y1="20" x2="420" y2="194" stroke="{ERROR}" '
               f'stroke-width="2" stroke-dasharray="5 5"/>')
    svg.append(f'<circle cx="420" cy="107" r="30" fill="#fff" stroke="{ERROR}" stroke-width="2"/>')
    svg.append(f'<text x="420" y="104" fill="{ERROR}" font-size="20" font-weight="bold" '
               f'text-anchor="middle">≠</text>')
    svg.append(f'<text x="420" y="120" fill="{ERROR}" font-size="8" font-weight="bold" '
               f'text-anchor="middle">НЕ смешивать</text>')
    svg.append('</svg>')
    return "".join(svg)

# ══════════════════════════════════════════════════════════════════════════════
# Таблицы
# ══════════════════════════════════════════════════════════════════════════════
def data_table(headers, rows):
    h = "".join(f"<th>{x}</th>" for x in headers)
    body = ""
    for r in rows:
        cells = ""
        for i, c in enumerate(r):
            cls = ' class="k"' if i == 0 else ""
            cells += f"<td{cls}>{c}</td>"
        body += f"<tr>{cells}</tr>"
    return (f'<div class="tablewrap"><table class="data"><thead><tr>{h}</tr></thead>'
            f'<tbody>{body}</tbody></table></div>')

# ══════════════════════════════════════════════════════════════════════════════
# Callout / пример / рекомендация / чек-пункт
# ══════════════════════════════════════════════════════════════════════════════
def callout(kind, head, body):
    ic = {"imp": ("warn", WARNING), "note": ("info", PRIMARY),
          "tip": ("check", ACCENT), "risk": ("risk", ERROR)}[kind]
    return (f'<div class="callout c-{kind}"><div class="ic">{icon(ic[0], ic[1])}</div>'
            f'<div class="bd"><div class="hd">{head}</div>{body}</div></div>')

def example(title, tag, body):
    return (f'<div class="example"><div class="top">{title}<span class="tag">{tag}</span></div>'
            f'<div class="bdy">{body}</div></div>')

def rec(n, title, body):
    return f'<div class="rec"><div class="n">{n}</div><div class="rt">{title}</div><div class="rd">{body}</div></div>'

def check_item(text):
    return f'<div class="ci"><div class="box">{checkbox()}</div><div class="txt">{text}</div></div>'

# ══════════════════════════════════════════════════════════════════════════════
# Сборка контента
# ══════════════════════════════════════════════════════════════════════════════
def build_html():
    B = []
    A = B.append

    # ---------- ОБЛОЖКА ----------
    A(f'''
<div class="cover">
  <div class="frame"></div>
  <div class="wm">01</div>
  <div class="inner">
    <div style="padding:18mm 18mm;">
      <div class="eyebrow">MainExperts · Playbook</div>
      <div class="kicker">Корпоративный стандарт</div>
      <h1>Система получения<br/>отзывов<br/>MainExperts</h1>
      <div class="sub">Отзыв как стратегический актив компании,
        сопровождающей семью на всём пути — от выбора профессии подростком
        до его первого рабочего места.</div>
    </div>
  </div>
  <div class="ver">Версия <b>1.0</b>&nbsp;&nbsp;·&nbsp;&nbsp;Глава 1. Философия системы</div>
  <div class="meta">
    <div>Внутренний документ. Рабочий контекст, не выверенный источник —<br/>
      перед клиентскими материалами факт перепроверяется с источником и датой.</div>
    <div style="text-align:right">Дата выпуска: 07.07.2026<br/>Конфиденциально</div>
  </div>
</div>''')

    # ---------- О ПЛЕЙБУКЕ ----------
    A('<div class="newpage"></div>')
    A('<div class="eyebrow">О документе</div>')
    A('<h2>Как устроен этот плейбук</h2>')
    A('''<p class="lead-in">Плейбук — рабочий стандарт, а не теория. Он отвечает на три вопроса:
      <strong>зачем</strong> компании система отзывов, <strong>где</strong> и <strong>как</strong>
      она собирает свидетельства, и <strong>кто</strong> за это отвечает. Глава 1 закладывает
      философию: без неё любые механики сбора превращаются в разрозненные просьбы «оставьте отзыв».</p>''')

    A('<h3>Для кого</h3>')
    A('''<div class="audience">
      <div class="audrow">
        <div class="aud"><b>CEO / COO</b><br/>владелец системы и ресурса</div>
        <div class="aud"><b>CMO / Head of Marketing</b><br/>применение отзыва в воронке</div>
        <div class="aud"><b>Head of Customer Success</b><br/>сбор на пути сопровождения</div>
      </div>
      <div class="audrow">
        <div class="aud"><b>Сопровождение</b><br/>исполнители на этапах пути</div>
        <div class="aud"><b>Методологи</b><br/>достоверность и границы</div>
        <div class="aud"><b>Эксперты и маркетологи</b><br/>носители и распространители</div>
      </div>
    </div>''')

    A('<h3>Структура каждой главы — 11 элементов</h3>')
    toc_items = [
        ("Титульный лист главы", "визуальный вход в тему"),
        ("Цель главы", "что читатель сможет делать после"),
        ("Ключевые понятия", "единый язык и определения"),
        ("Основная часть", "содержание — раскрытие темы"),
        ("Схемы", "рисованные диаграммы и модели"),
        ("Таблицы", "структурированные данные"),
        ("Примеры", "как это выглядит в жизни компании"),
        ("Практические рекомендации", "что делать на практике"),
        ("Чек-лист", "самопроверка готовности"),
        ("Резюме", "главное в сжатом виде"),
        ("Переход к следующей главе", "логическая связка"),
    ]
    def toc_col(items, start):
        rr = ""
        for i, (t, d) in enumerate(items, start):
            rr += (f'<div class="row"><div class="num">{i:02d}</div>'
                   f'<div class="lbl"><b>{t}</b> — {d}</div></div>')
        return f'<div class="toc">{rr}</div>'
    A(f'<div class="toc2"><div class="toccol">{toc_col(toc_items[:6], 1)}</div>'
      f'<div class="toccol">{toc_col(toc_items[6:], 7)}</div></div>')
    A(callout("note", "Единый визуальный язык",
              "Пять цветов бренда несут смысл на всех страницах: "
              "<b>синий</b> — основное и структура, <b>тёмный</b> — акценты текста, "
              "<b>зелёный</b> — ценность и результат, <b>жёлтый</b> — «важно», "
              "<b>красный</b> — риск и запрет («не смешивать потоки»). Схемы всегда нарисованы, "
              "а не описаны словами."))

    # ---------- 1. ТИТУЛ ГЛАВЫ ----------
    A(f'''
<div class="chapter-title">
  <div class="no">Глава 1</div>
  <div class="bar"></div>
  <h1>Философия системы<br/>получения отзывов<br/>MainExperts</h1>
  <div class="lead">Почему для компании, которая сопровождает семью годами, отзыв —
    не любезность клиента в конце, а стратегический актив, который собирается на всём пути
    и работает на доверие, выручку и качество сопровождения.</div>
  <div class="foot">
    <div>PLAYBOOK · Система получения отзывов MainExperts · Версия 1.0</div>
    <div>Глава 1&nbsp;·&nbsp;Философия системы</div>
  </div>
</div>''')

    # ---------- 2. ЦЕЛЬ ----------
    A('<section>')
    A('<span class="eltag accent">02 · Цель главы</span>')
    A('<h2>Цель главы</h2>')
    A('''<div class="goalbox"><div class="big">Сформировать у всей команды единое понимание:
      <strong>отзыв — это управляемый стратегический актив компании</strong>, а не побочный
      продукт удачной услуги. После главы читатель различает отзыв-«событие» и отзыв-«актив»,
      понимает, почему длинный путь сопровождения делает свидетельство критически важным,
      и видит, где отзыв рождается и где он работает — раздельно для двух клиентов и двух
      потоков выручки.</div></div>''')
    A('''<p style="margin-top:9pt">Это не инструкция «как попросить отзыв». Это фундамент,
      на котором в следующих главах строятся карта точек сбора, роли, форматы и метрики.
      Механика без философии даёт разрозненные просьбы; философия без механики остаётся
      лозунгом. Глава 1 закрывает первую половину.</p>''')
    A('</section>')

    # ---------- 3. КЛЮЧЕВЫЕ ПОНЯТИЯ ----------
    A('<section class="newpage">')
    A('<span class="eltag">03 · Ключевые понятия</span>')
    A('<h2>Ключевые понятия</h2>')
    A('<p class="lead-in">Единый язык — первое условие системы. Ниже — термины, которыми '
      'мы пользуемся во всём плейбуке.</p>')
    concepts = [
        ("Отзыв-свидетельство", "Задокументированное свидетельство изменения в жизни семьи "
         "или в работе эксперта: «было → стало». Не оценка «понравилось / нет», а факт пути.",
         "ядро системы"),
        ("Актив vs событие", "Событие — разовая похвала, которая теряется. Актив — "
         "свидетельство, которое собрано, сохранено и работает на компанию годами.",
         "различение №1"),
        ("Путь сопровождения", "Длинная траектория семьи от выбора профессии подростком "
         "до его первого места работы. 11 этапов, каждый — точка ценности и точка отзыва.",
         "контекст продукта"),
        ("Два клиента", "Семьи (родители и подросток) и Эксперты. У каждого — свой голос: "
         "семья свидетельствует о результате, эксперт — о процессе и платформе.",
         "два источника"),
        ("Два потока", "Founder Premium (личные продажи HNW) и Platform (воронка). "
         "Отзыв работает в обоих, но механикой и метриками они не смешиваются.",
         "жёсткое правило"),
        ("Петля ценности", "Свидетельство возвращается в компанию как знание и улучшает "
         "продукт и сопровождение — по методологии управления ценностью V4.1.",
         "обратная связь"),
    ]
    A('<div class="grid2">')
    for i in range(0, len(concepts), 2):
        A('<div class="grow">')
        for term, dfn, tag in concepts[i:i+2]:
            A(f'<div class="gcell"><div class="concept"><div class="term">{term}</div>'
              f'<div class="def">{dfn}</div><span class="tagline">{tag}</span></div></div>')
        A('</div>')
    A('</div>')
    A('</section>')

    # ---------- 4. ОСНОВНАЯ ЧАСТЬ + 5. СХЕМЫ ----------
    A('<section class="newpage">')
    A('<span class="eltag dark">04 · Основная часть</span>')
    A('<h2>Почему отзыв для MainExperts — стратегия, а не любезность</h2>')

    A('<h3>Что такое MainExperts на самом деле</h3>')
    A('''<div class="sidenote"><div class="t">Ставка, а не факт</div>
      Центральная гипотеза проекта — «скрининг оцифровывает страхи родителя, и родитель
      покупает диагностику, чтобы их закрыть» — пока <b>не подтверждена</b>. Система отзывов —
      именно тот механизм, который может её проверить: если свидетельства показывают снятую
      тревогу, гипотеза получает опору. До этого — помечаем как ставку.</div>''')
    A('''<p>MainExperts — не разовая услуга «сделали профориентацию и попрощались».
      Это платформа, которая <strong>сопровождает семью годами</strong>: от первого вопроса
      «кем быть» до момента, когда вчерашний подросток выходит на первое рабочее место.
      Между этими точками — профориентация, диагностика, выбор профессии и университета,
      обучение и дополнительные предметы, поступление, визовая поддержка, релокация,
      адаптация. Одиннадцать этапов одного пути.</p>''')
    A('''<p>Из этого вырастает всё остальное. Родитель платит <strong>заранее — за будущее
      ребёнка, которого ещё нет</strong>. В точке решения у него нет результата на руках;
      есть только тревога и цена ошибки. Единственное, что снижает эту тревогу, — свидетельство
      другой семьи, которая этот путь уже прошла. Поэтому отзыв здесь — не финальный
      «спасибо», а условие самой продажи.</p>''')

    A(f'<figure><div class="schema">{schema_journey()}<figcaption>'
      f'<b>Схема 1.</b> Путь сопровождения семьи: три фазы, одиннадцать этапов. '
      f'Свидетельство собирается вдоль всего пути, а не только на выходе — каждая точка '
      f'ценности является потенциальной точкой отзыва.</figcaption></div></figure>')

    A('<h3>Два клиента — два голоса</h3>')
    A('''<p>У компании два клиента, и это не деталь, а развилка всей системы. <strong>Семьи</strong>
      свидетельствуют о результате: что изменилось в ребёнке и в спокойствии родителя.
      <strong>Эксперты</strong> свидетельствуют о процессе и о платформе: работает ли методика,
      удобен ли инструмент, честна ли экономика. Это два разных отзыва, с разным содержанием
      и разным применением — их нельзя собирать одним шаблоном.</p>''')
    A(f'<figure><div class="schema">{schema_two_clients()}<figcaption>'
      f'<b>Схема 2.</b> Два источника свидетельств. Голос семьи доказывает результат новым '
      f'семьям; голос эксперта калибрует сеть и подтверждает компетенцию. Смешивать их '
      f'в один поток — терять смысл обоих.</figcaption></div></figure>')

    A('<h3>Отзыв как актив: накопительный эффект</h3>')
    A('''<p>Разовая похвала в переписке греет самолюбие и исчезает. Свидетельство, которое
      собрано, оформлено и сохранено, начинает работать как <strong>актив на балансе доверия</strong>:
      снижает стоимость привлечения новой семьи, повышает конверсию на входе в воронку,
      укрепляет позиции эксперта и возвращается в продукт как знание. Один раз собранный отзыв
      работает годами — и чем их больше, тем сильнее эффект. Отсюда — рабочая петля ценности.</p>''')
    A(f'<figure><div class="schema">{schema_value_loop()}<figcaption>'
      f'<b>Схема 3.</b> Петля ценности отзыва. Впечатление на этапе превращается в '
      f'свидетельство, свидетельство пополняет актив, актив снижает риск у новой семьи и '
      f'возвращается в компанию как знание — цикл повторяется с накоплением.</figcaption></div></figure>')

    A('<h3>Два потока — две механики (не смешивать)</h3>')
    A('''<p>Отзыв работает в обоих потоках выручки, но <strong>совершенно по-разному</strong>,
      и это жёсткое правило компании. В <strong>потоке премиальных личных продаж</strong>
      свидетельство — это приватная рекомендация внутри узкого круга, валюта репутации;
      оно не публикуется и не выносится в воронку. В <strong>потоке воронки</strong> отзыв —
      публичное социальное доказательство, которое живёт на лендинге и в рассылке и снижает
      стоимость лида. Механики, метрики и даже само определение «хорошего отзыва» у них разные.</p>''')
    A(f'<figure><div class="schema">{schema_two_streams()}<figcaption>'
      f'<b>Схема 4.</b> Одна философия — две механики. Приватная рекомендация премиального '
      f'потока и публичное доказательство воронки не смешиваются ни в сборе, ни в применении, '
      f'ни в отчётности.</figcaption></div></figure>')

    A(callout("imp", "Важно · правило двух потоков",
              "Метрики и свидетельства двух потоков <b>никогда не объединяются</b>. "
              "Публичный отзыв из воронки нельзя выдавать за премиальную рекомендацию, а "
              "приватную рекомендацию HNW-круга — публиковать как соц. доказательство. "
              "Это разные каналы с разной экономикой и разными обязательствами перед клиентом."))

    A('<h3>Восемь принципов философии отзыва</h3>')
    A('<p class="lead-in">Всё сказанное сворачивается в восемь принципов — на них опираются '
      'механики следующих глав.</p>')
    principles = [
        ("Актив, а не побочный продукт", "Отзывом управляют системно, как ресурсом, а не собирают случайно."),
        ("Весь путь, а не финал", "Свидетельство собирается на каждом этапе, а не один раз в конце."),
        ("Свидетельство, а не оценка", "Фиксируем изменение «было → стало», а не «понравилось / нет»."),
        ("Два клиента — два голоса", "Голос семьи — о результате, голос эксперта — о процессе. Раздельно."),
        ("Два потока — две механики", "Приватная рекомендация и публичное доказательство не смешиваются."),
        ("Достоверность выше объёма", "Один проверяемый отзыв с источником ценнее десяти анонимных."),
        ("Этика прежде всего", "Данные несовершеннолетних, согласие и границы диагностики — нерушимы."),
        ("Замкнутая петля", "Отзыв возвращается в продукт как знание (V4.1), а не только в маркетинг."),
    ]
    A('<div class="tablewrap"><table class="data"><thead><tr>'
      '<th style="width:34pt">№</th><th style="width:33%">Принцип</th><th>Что он означает на практике</th>'
      '</tr></thead><tbody>')
    for i, (t, d) in enumerate(principles, 1):
        A(f'<tr><td class="k">{i}</td><td class="k">{t}</td><td>{d}</td></tr>')
    A('</tbody></table></div>')
    A('</section>')

    # ---------- 6. ТАБЛИЦЫ ----------
    A('<section>')
    A('<span class="eltag">06 · Таблицы</span>')
    A('<h2>Где рождается и где работает отзыв</h2>')
    A('<p class="lead-in">Сводная таблица связывает этап пути, содержание свидетельства и '
      'место его применения. Метка потока показывает, в какой механике отзыв уместен.</p>')
    A(data_table(
        ["Этап пути", "Что свидетельствует", "Где работает", "Поток"],
        [
            ["Профориентация и диагностика",
             "«Ребёнка впервые услышали», снятая растерянность",
             "Вход в воронку, лендинг скрининга", '<span class="pill p2">П2</span>'],
            ["Выбор профессии и университета",
             "Ясность вместо тревоги, обоснованное решение",
             "Кейсы, апсейл на диагностику", '<span class="pill both">оба</span>'],
            ["Обучение и поступление",
             "Достигнутый результат: поступление, прогресс",
             "Публичные истории, отчёт", '<span class="pill p2">П2</span>'],
            ["Визы, релокация, адаптация",
             "Компания не бросила на сложном отрезке",
             "Премиальная рекомендация", '<span class="pill p1">П1</span>'],
            ["Первое место работы",
             "Финальное «путь сработал» — сильнейшее свидетельство",
             "Флагманский кейс, оба потока", '<span class="pill both">оба</span>'],
            ["Работа эксперта (сквозной)",
             "Качество методики и платформы в деле",
             "Калибровка сети, найм экспертов", '<span class="pill p2">П2</span>'],
        ]))
    A('<div class="small" style="margin-top:-4pt">П1 — Founder Premium (приватно); '
      'П2 — Platform (публично); «оба» — уместно в обеих механиках при раздельном оформлении.</div>')

    A('<h3>Отзыв-событие против отзыва-актива</h3>')
    A(data_table(
        ["Параметр", "Отзыв-событие", "Отзыв-актив"],
        [
            ["Горизонт", "разовый, живёт минуты", "накопительный, работает годами"],
            ["Управление", "случайный, по настроению", "системный, по регламенту"],
            ["Форма", "реплика в переписке", "оформленное свидетельство «было → стало»"],
            ["Ценность", "приятно, но не масштабируется", "снижает CAC, растит конверсию и доверие"],
            ["Судьба", "теряется", "сохранён, размечен, переиспользуется"],
        ]))
    A('</section>')

    # ---------- 7. ПРИМЕРЫ ----------
    A('<section>')
    A('<span class="eltag dark">07 · Примеры</span>')
    A('<h2>Как это выглядит в жизни компании</h2>')
    A(example("Пример 1. Родитель на входе в воронку", "Поток 2 · публично",
              '<div class="step">Мать 14-летнего подростка колеблется на лендинге скрининга: '
              'платить ли за диагностику будущего ребёнка.</div>'
              '<div class="step">Рядом — свидетельство другой семьи, чей сын прошёл путь до '
              'поступления: <span class="bef">было</span> — «не понимали, куда он вообще»; '
              '<span class="aft">стало</span> — «выбрал направление осознанно и поступил».</div>'
              '<div class="step"><b>Эффект:</b> воспринимаемый риск падает, тревога получает '
              'опору, конверсия входа в скрининг растёт. Отзыв здесь — часть продающей логики, '
              'а не украшение.</div>'))
    A(example("Пример 2. Свидетельство эксперта", "Поток 2 · сеть",
              '<div class="step">Эксперт после сопровождения оставляет отзыв о процессе: '
              'методика применима, платформа не мешает, экономика прозрачна.</div>'
              '<div class="step"><b>Эффект:</b> отзыв идёт не в маркетинг, а в калибровку сети '
              'и в найм новых экспертов как доказательство того, что «здесь можно работать '
              'честно». Голос эксперта решает другую задачу, чем голос семьи.</div>'))
    A(example("Пример 3. Премиальная рекомендация", "Поток 1 · приватно · не публикуется",
              '<div class="step">Семья из премиального круга проходит полный путь, включая визы '
              'и релокацию, и рекомендует компанию знакомой семье того же круга.</div>'
              '<div class="step"><b>Эффект:</b> рекомендация работает как валюта доверия внутри '
              'сети HNW. Её <b>нельзя</b> вынести на лендинг или превратить в публичный кейс — '
              'это нарушило бы и правило двух потоков, и обязательства перед клиентом.</div>'))
    A(callout("tip", "Общий знаменатель трёх примеров",
              "Во всех случаях ценность несёт не похвала, а <b>зафиксированное изменение</b> "
              "и <b>правильный адрес применения</b>. Один и тот же факт в неверной механике "
              "теряет силу или нарушает правило."))
    A('</section>')

    # ---------- 8. ПРАКТИЧЕСКИЕ РЕКОМЕНДАЦИИ ----------
    A('<section>')
    A('<span class="eltag accent">08 · Практические рекомендации</span>')
    A('<h2>Что делать с этой философией на практике</h2>')
    A('<p class="lead-in">Девять установок, которые переводят принципы в поведение команды '
      'уже сегодня — до появления автоматизации.</p>')
    recs = [
        ("Встройте сбор в путь", "Планируйте точку отзыва на каждом этапе сопровождения, а не «когда вспомним»."),
        ("Спрашивайте «было → стало»", "Фиксируйте изменение, а не удовлетворённость. Это и есть свидетельство."),
        ("Разведите два голоса", "Разные вопросы и форматы для семьи и для эксперта. Не один шаблон."),
        ("Держите потоки раздельно", "Публичное — в воронку, приватное — в круг. Никогда не переносить между ними."),
        ("Берите согласие явно", "Особенно на данные подростка. Без согласия свидетельства не существует."),
        ("Проверяемость обязательна", "У отзыва есть источник и дата. Анонимную похвалу активом не считаем."),
        ("Не гонитесь за объёмом", "Десять честных сильнее ста наведённых. Достоверность — первый приоритет."),
        ("Возвращайте в продукт", "Свидетельства читает не только маркетинг: это вход в улучшение сопровождения."),
        ("Считайте отзыв ресурсом", "У актива есть владелец и место хранения. Назначьте их до старта сбора."),
    ]
    for i in range(0, len(recs), 3):
        A('<div class="recs">')
        for j, (t, d) in enumerate(recs[i:i+3], i+1):
            A(rec(j, t, d))
        A('</div>')
    A(callout("risk", "Осторожно · чего не делать",
              "Не покупайте и не «наводите» отзывы, не публикуйте свидетельства без согласия, "
              "не выдавайте оценку транзакции за свидетельство пути и <b>никогда</b> не смешивайте "
              "приватную премиальную рекомендацию с публичным контентом воронки."))
    A('</section>')

    # ---------- 9. ЧЕК-ЛИСТ ----------
    A('<section>')
    A('<span class="eltag">09 · Чек-лист</span>')
    A('<h2>Самопроверка: готовы ли собирать отзыв как актив</h2>')
    A('<p class="lead-in">Пройдите список прежде, чем запускать механики следующих глав. '
      'Каждый непоставленный флажок — риск превратить систему в набор случайных просьб.</p>')
    A('<div class="checklist">')
    checks = [
        "Команда различает <b>отзыв-событие</b> и <b>отзыв-актив</b> и говорит на одном языке.",
        "Для каждого из <b>11 этапов пути</b> определено, какое свидетельство на нём рождается.",
        "Разделены <b>два голоса</b>: отдельные вопросы для семьи и для эксперта.",
        "Зафиксировано правило <b>двух потоков</b>: что публично, что приватно, и почему.",
        "Формат отзыва требует изменения <b>«было → стало»</b>, а не оценки «понравилось».",
        "Определён порядок <b>согласия</b>, включая данные несовершеннолетних.",
        "У каждого отзыва есть <b>источник и дата</b>; анонимное активом не считается.",
        "Назначены <b>владелец</b> актива отзывов и <b>место хранения</b>.",
        "Понятно, как свидетельство <b>возвращается в продукт</b> (петля ценности V4.1).",
        "Гипотеза скрининга помечена как <b>ставка</b>, и отзыв рассматривается как её проверка.",
    ]
    for c in checks:
        A(check_item(c))
    A('</div>')
    A('</section>')

    # ---------- 10. РЕЗЮМЕ ----------
    A('<section>')
    A('<span class="eltag dark">10 · Резюме</span>')
    A('<h2>Главное из главы 1</h2>')
    A('''<div class="summary"><h3>Отзыв — стратегический актив длинного пути</h3>
      <ol>
        <li><b>Длинный путь меняет роль отзыва.</b> Родитель платит за будущее заранее —
          свидетельство другой семьи снижает тревогу и становится условием продажи.</li>
        <li><b>Актив, а не событие.</b> Собранное и сохранённое свидетельство работает годами:
          снижает стоимость привлечения, растит конверсию и доверие.</li>
        <li><b>Два клиента — два голоса.</b> Семья свидетельствует о результате, эксперт —
          о процессе и платформе. Разное содержание, разное применение.</li>
        <li><b>Два потока — две механики.</b> Приватная премиальная рекомендация и публичное
          доказательство воронки не смешиваются никогда.</li>
        <li><b>Достоверность и этика — рамка.</b> Источник, дата, согласие и «было → стало»
          важнее объёма; отзыв замыкает петлю ценности и возвращается в продукт.</li>
      </ol></div>''')
    A('</section>')

    # ---------- 11. ПЕРЕХОД ----------
    A('<section>')
    A('<span class="eltag">11 · Переход к следующей главе</span>')
    A('<div class="divider"><span class="dot"></span></div>')
    A(f'''<div class="transition">
      <div class="l">
        <div class="nx">Далее · Глава 2</div>
        <h3>Карта точек сбора: где и как система собирает отзыв</h3>
        <p>Философия отвечает на вопрос «зачем». Глава 2 переводит его в «где и как»:
          разложим одиннадцать этапов пути на конкретные точки контакта, определим формат
          свидетельства для каждой и разведём механику сбора по двум потокам и двум клиентам.</p>
      </div>
      <div class="r">
        <svg viewBox="0 0 48 48" width="48" height="48" xmlns="http://www.w3.org/2000/svg">
          <circle cx="24" cy="24" r="22" fill="none" stroke="{PRIMARY}" stroke-width="2"/>
          <path d="M20 15 L30 24 L20 33" fill="none" stroke="{PRIMARY}" stroke-width="3"
            stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </div>''')
    A('</section>')

    return "\n".join(B)


def main():
    html_body = build_html()
    # string-set для колонтитула главы
    doc = f'''<!doctype html><html lang="ru"><head><meta charset="utf-8">
<style>{CSS}
.chapter-title h1 {{ string-set: chaptitle "Глава 1 · Философия системы получения отзывов"; }}
</style></head><body>{html_body}</body></html>'''
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(HTML_DEBUG, "w", encoding="utf-8") as f:
        f.write(doc)
    pdf_path = os.path.join(OUT_DIR, PDF_NAME)
    HTML(string=doc, base_url=OUT_DIR).write_pdf(pdf_path)
    print("HTML :", HTML_DEBUG)
    print("PDF  :", pdf_path, os.path.getsize(pdf_path), "bytes")


if __name__ == "__main__":
    main()
