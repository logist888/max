#!/usr/bin/env python3
"""Markdown-документ с таблицами → PDF в стиле Demo Day (A4 альбомная, DejaVu Sans).

Поддержка: заголовки # ## ###, абзацы, списки «- » и «1. », таблицы GFM (| a | b |),
**жирный**, *курсив*, `код`, горизонтальная линия ---. Тёмная титульная страница,
светлые страницы содержания, золотые акценты, колонтитулы с номером страницы.
Запуск: python3 scripts/build_doc_pdf.py <вход.md> <выход.pdf> ["Надзаголовок"]
"""
import os, re, sys, io
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, NextPageTemplate, KeepTogether, HRFlowable)

FD = "/usr/share/fonts/truetype/dejavu/"
def _reg(n, f, fb):
    p = FD + f
    if not os.path.exists(p): p = FD + fb
    pdfmetrics.registerFont(TTFont(n, p))
_reg("DV", "DejaVuSans.ttf", "DejaVuSans.ttf"); _reg("DV-B", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf")
_reg("DV-I", "DejaVuSans-Oblique.ttf", "DejaVuSans.ttf"); _reg("DV-BI", "DejaVuSans-BoldOblique.ttf", "DejaVuSans-Bold.ttf")
registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

INK = colors.HexColor("#101010"); LIGHT = colors.HexColor("#f8f8f8"); CARD = colors.white
GOLD = colors.HexColor("#c0a870"); GOLD_D = colors.HexColor("#8f7640"); GOLD_L = colors.HexColor("#ede3cc")
GREY_L = colors.HexColor("#c8c8c8"); GREY_T = colors.HexColor("#5f5f5f"); LINE = colors.HexColor("#e0e0e0"); ZEBRA = colors.HexColor("#f1f1f1")

PW, PH = landscape(A4)
ML = MR = 36; MT = 44; MB = 34; W = PW - ML - MR
TOTAL = [0]; LABEL = ["MAINEXPERTS"]

def st(name, **kw):
    base = dict(fontName="DV", fontSize=9, leading=12.4, textColor=INK, alignment=TA_LEFT, spaceAfter=5)
    base.update(kw); return ParagraphStyle(name, **base)
S = {
    "h1": st("h1", fontName="DV-B", fontSize=17, leading=21, spaceBefore=6, spaceAfter=6),
    "h2": st("h2", fontName="DV-B", fontSize=12.5, leading=16, spaceBefore=10, spaceAfter=4, textColor=INK),
    "h3": st("h3", fontName="DV-B", fontSize=10, leading=13, spaceBefore=7, spaceAfter=3, textColor=GOLD_D),
    "body": st("body"),
    "bul": st("bul", leftIndent=12, bulletIndent=2, spaceAfter=2.5),
    "cell": st("cell", fontSize=7.4, leading=9.6, spaceAfter=0),
    "cellb": st("cellb", fontName="DV-B", fontSize=7.4, leading=9.6, spaceAfter=0),
    "head": st("head", fontName="DV-B", fontSize=7.2, leading=9.2, textColor=LIGHT, spaceAfter=0),
    "titled": st("titled", fontName="DV-B", fontSize=30, leading=35, textColor=LIGHT, spaceAfter=8),
    "subd": st("subd", fontSize=11, leading=15, textColor=GREY_L, spaceAfter=6),
    "bodyd": st("bodyd", fontSize=9.5, leading=13, textColor=LIGHT),
}

def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"`([^`]+)`", r"<font face='DV' color='#8f7640'>\1</font>", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    return t

def split_row(line):
    line = line.strip()
    if line.startswith("|"): line = line[1:]
    if line.endswith("|"): line = line[:-1]
    return [c.strip() for c in line.split("|")]

def col_widths(rows, ncol):
    lens = [1] * ncol; longest = [1] * ncol
    for r in rows:
        for i in range(ncol):
            txt = r[i] if i < len(r) else ""
            lens[i] = max(lens[i], min(len(txt), 220))
            for w in re.split(r"[\s/,;]+", txt):
                longest[i] = max(longest[i], len(w))
    weights = [max(6, l ** 0.75) for l in lens]
    total = sum(weights)
    widths = [W * w / total for w in weights]
    # минимальная ширина: самое длинное слово колонки в 7,4 pt плюс отступы
    mins = [min(W * 0.3, longest[i] * 4.3 + 12) for i in range(ncol)]
    for i in range(ncol):
        if widths[i] < mins[i]:
            deficit = mins[i] - widths[i]; widths[i] = mins[i]
            others = [j for j in range(ncol) if j != i and widths[j] > mins[j]]
            pool = sum(widths[j] - mins[j] for j in others) or 1
            for j in others: widths[j] -= deficit * (widths[j] - mins[j]) / pool
    return widths

def make_table(head, rows):
    ncol = len(head)
    norm = [r + [""] * (ncol - len(r)) for r in rows]
    widths = col_widths([head] + norm, ncol)
    data = [[Paragraph(inline(h), S["head"]) for h in head]]
    for r in norm:
        data.append([Paragraph(inline(c), S["cellb"] if i == 0 else S["cell"]) for i, c in enumerate(r[:ncol])])
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("BACKGROUND", (0, 1), (-1, -1), CARD),
             ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
             ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    for i in range(2, len(data), 2): style.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    t.setStyle(TableStyle(style)); return t

def parse(md):
    """Возвращает (title, subtitle_lines, flowables)."""
    lines = md.splitlines(); F = []; title = None; intro = []
    i = 0; para = []
    def flush_para():
        nonlocal para
        if para:
            F.append(Paragraph(inline(" ".join(para)), S["body"])); para = []
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("# ") and title is None:
            title = ln[2:].strip(); i += 1
            # абзацы до первого ## — во вступление на титул
            while i < len(lines) and not lines[i].startswith("## "):
                if lines[i].strip(): intro.append(lines[i].strip())
                i += 1
            continue
        if ln.strip() == "" :
            flush_para(); i += 1; continue
        if ln.startswith("## "):
            flush_para(); F.append(Paragraph(inline(ln[3:]), S["h2"])); F.append(HRFlowable(width="100%", thickness=0.6, color=GOLD, spaceAfter=4)); i += 1; continue
        if ln.startswith("### "):
            flush_para(); F.append(Paragraph(inline(ln[4:]), S["h3"])); i += 1; continue
        if ln.strip() == "---":
            flush_para(); F.append(HRFlowable(width="100%", thickness=0.4, color=LINE, spaceBefore=4, spaceAfter=4)); i += 1; continue
        if ln.lstrip().startswith("|"):
            flush_para(); rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(split_row(lines[i])); i += 1
            if len(rows) >= 2 and all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in rows[1] if c.strip()):
                head, body = rows[0], rows[2:]
            else:
                head, body = rows[0], rows[1:]
            F.append(make_table(head, body)); F.append(Spacer(1, 6)); continue
        m = re.match(r"^\s*([-*]|\d+\.)\s+(.*)", ln)
        if m:
            flush_para()
            bullet = "•" if m.group(1) in "-*" else m.group(1)
            txt = m.group(2); i += 1
            while i < len(lines) and lines[i].startswith("  ") and not re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                txt += " " + lines[i].strip(); i += 1
            F.append(Paragraph(inline(txt), S["bul"], bulletText=bullet)); continue
        if ln.startswith("_") and ln.endswith("_"):
            F.append(Paragraph("<i>" + inline(ln.strip("_")) + "</i>", S["body"])); i += 1; continue
        para.append(ln.strip()); i += 1
    flush_para()
    return title, intro, F

def _frame(): return Frame(ML, MB, W, PH - MT - MB, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
def _chrome(c, doc, bg, fg, mut):
    c.saveState(); c.setFillColor(bg); c.rect(0, 0, PW, PH, stroke=0, fill=1)
    c.setFont("DV-B", 7.5); c.setFillColor(fg); c.drawString(ML, PH - 24, "MAINEXPERTS")
    c.setFont("DV", 6.8); c.setFillColor(mut); c.drawRightString(PW - MR, PH - 24, LABEL[0])
    c.setStrokeColor(GOLD if bg == INK else LINE); c.setLineWidth(0.5); c.line(ML, PH - 30, PW - MR, PH - 30)
    c.setFont("DV", 6.6); c.setFillColor(mut)
    c.drawString(ML, 14, "Внутренний документ · значения для России — рабочие значения пилота · правовые пункты — вопросы к юристу, не заключения")
    c.drawRightString(PW - MR, 14, f"{doc.page:02d} / {TOTAL[0]:02d}")
    c.restoreState()
def on_light(c, doc): _chrome(c, doc, LIGHT, INK, GREY_T)
def on_dark(c, doc): _chrome(c, doc, INK, LIGHT, GREY_L)

class Pill(Paragraph):
    pass

def story(md, label):
    title, intro, body = parse(md)
    F = [NextPageTemplate("dark"), Spacer(1, 70)]
    t = Table([[Paragraph(label.upper(), ParagraphStyle("p", fontName="DV-B", fontSize=6.5, textColor=INK))]], colWidths=[pdfmetrics.stringWidth(label.upper(), "DV-B", 6.5) + 16])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GOLD), ("ROUNDEDCORNERS", [5, 5, 5, 5]), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    F += [t, Spacer(1, 12), Paragraph(inline(title or ""), S["titled"])]
    for p in intro[:1]: F.append(Paragraph(inline(p), S["subd"]))
    F.append(Spacer(1, 10))
    for p in intro[1:]: F.append(Paragraph(inline(p), S["bodyd"])); F.append(Spacer(1, 4))
    F += [NextPageTemplate("light"), PageBreak()]
    F += body
    return F

def build(md_path, out, label):
    LABEL[0] = label
    md = open(md_path, encoding="utf-8").read()
    def make(target):
        doc = BaseDocTemplate(target, pagesize=(PW, PH), leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB, title=label, author="MainExperts")
        doc.addPageTemplates([PageTemplate(id="dark", frames=[_frame()], onPage=on_dark), PageTemplate(id="light", frames=[_frame()], onPage=on_light)])
        return doc
    d1 = make(io.BytesIO()); d1.build(story(md, label)); TOTAL[0] = d1.page
    d2 = make(out); d2.build(story(md, label)); return d2.page

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    n = build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "MainExperts · документ")
    print("PDF:", sys.argv[2], "pages:", n, "bytes:", os.path.getsize(sys.argv[2]))
