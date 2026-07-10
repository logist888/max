#!/usr/bin/env python3
"""Markdown-ish -> PDF с кириллицей (DejaVu Sans).

Использование:
    python3 scripts/pdf_ru.py <draft.md> <out.pdf> ["Заголовок"]

Поддержка: заголовки '# ## ###', списки '- ', цитаты '> ', **жирный**, *курсив*,
пустая строка = разрыв абзаца, таблицы '| a | b |' (строка-разделитель |---|
пропускается, первая строка — шапка), огороженные блоки ``` (моноширинно, язык
игнорируется). Шрифт DejaVu Sans (все доступные начертания); если нет
oblique-файлов — курсив деградирует до прямого (функционально не критично).
"""
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)

FONTDIR = "/usr/share/fonts/truetype/dejavu/"
CONTENT_W = (210 - 22 - 20) * mm  # A4 минус поля документа


def _register(name: str, filename: str, fallback: str) -> None:
    path = FONTDIR + filename
    if not os.path.exists(path):
        path = FONTDIR + fallback
        sys.stderr.write(f"[pdf_ru] {filename} нет — заменён на {fallback}\n")
    pdfmetrics.registerFont(TTFont(name, path))


_register("DejaVu", "DejaVuSans.ttf", "DejaVuSans.ttf")
_register("DejaVu-Bold", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf")
_register("DejaVu-Italic", "DejaVuSans-Oblique.ttf", "DejaVuSans.ttf")
_register("DejaVu-BoldItalic", "DejaVuSans-BoldOblique.ttf", "DejaVuSans-Bold.ttf")
_register("DejaVu-Mono", "DejaVuSansMono.ttf", "DejaVuSans.ttf")
registerFontFamily(
    "DejaVu",
    normal="DejaVu",
    bold="DejaVu-Bold",
    italic="DejaVu-Italic",
    boldItalic="DejaVu-BoldItalic",
)


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(text: str) -> str:
    text = esc(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r'<font name="DejaVu-Mono" size="8.5">\1</font>', text)
    return text


def _styles():
    ss = getSampleStyleSheet()
    body = ParagraphStyle(
        "body", parent=ss["Normal"], fontName="DejaVu",
        fontSize=10.5, leading=15, alignment=TA_LEFT, spaceAfter=6,
    )
    h1 = ParagraphStyle("h1", parent=body, fontName="DejaVu-Bold",
                        fontSize=17, leading=22, spaceBefore=6, spaceAfter=10)
    h2 = ParagraphStyle("h2", parent=body, fontName="DejaVu-Bold",
                        fontSize=13.5, leading=18, spaceBefore=10, spaceAfter=6)
    h3 = ParagraphStyle("h3", parent=body, fontName="DejaVu-Bold",
                        fontSize=11.5, leading=16, spaceBefore=8, spaceAfter=4)
    quote = ParagraphStyle("quote", parent=body, leftIndent=10,
                           textColor="#555555", fontName="DejaVu-Italic")
    cell = ParagraphStyle("cell", parent=body, fontSize=8, leading=10.5,
                          spaceAfter=0)
    cell_h = ParagraphStyle("cell_h", parent=cell, fontName="DejaVu-Bold")
    code = ParagraphStyle("code", parent=body, fontName="DejaVu-Mono",
                          fontSize=7.5, leading=9.5, leftIndent=6,
                          backColor="#f4f4f4", borderPadding=4, spaceAfter=6)
    return body, h1, h2, h3, quote, cell, cell_h, code


def _split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_sep_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c) and any(cells)


def _table(rows: list[list[str]], cell, cell_h) -> Table:
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    # ширины пропорционально типичной длине содержимого, с нижним порогом
    weights = []
    for j in range(ncols):
        lens = sorted(len(rows[i][j]) for i in range(len(rows)))
        weights.append(max(4, lens[int(0.9 * (len(lens) - 1))]))
    total = sum(weights)
    min_w = 13 * mm
    widths = [max(min_w, CONTENT_W * w / total) for w in weights]
    over = sum(widths) - CONTENT_W
    if over > 0:  # ужать самые широкие колонки
        wide = [i for i, w in enumerate(widths) if w > min_w]
        pool = sum(widths[i] - min_w for i in wide)
        for i in wide:
            widths[i] -= over * (widths[i] - min_w) / pool
    data = [[Paragraph(inline(c), cell_h if i == 0 else cell) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build(md: str, out: str, title: str | None = None) -> None:
    body, h1, h2, h3, quote, cell, cell_h, code = _styles()
    flow: list = []
    bullets: list = []
    table_rows: list = []
    code_lines: list | None = None  # None = вне блока ```

    def flush():
        if bullets:
            flow.append(ListFlowable(
                [ListItem(Paragraph(inline(b), body)) for b in bullets],
                bulletType="bullet", start="•",
            ))
            bullets.clear()
        if table_rows:
            flow.append(_table(list(table_rows), cell, cell_h))
            flow.append(Spacer(1, 6))
            table_rows.clear()

    if title:
        flow.append(Paragraph(inline(title), h1))
        flow.append(Spacer(1, 4))

    for raw in md.splitlines():
        line = raw.rstrip()
        if code_lines is not None:
            if line.strip().startswith("```"):
                flow.append(XPreformatted(esc("\n".join(code_lines)), code))
                code_lines = None
            else:
                code_lines.append(raw)
            continue
        if line.strip().startswith("```"):
            flush()
            code_lines = []
            continue
        if line.lstrip().startswith("|") and "|" in line.lstrip()[1:]:
            cells = _split_row(line)
            if not _is_sep_row(cells):
                table_rows.append(cells)
            continue
        if line.startswith(("- ", "* ")):
            if table_rows:
                flush()
            bullets.append(line[2:])
            continue
        flush()
        if not line.strip():
            flow.append(Spacer(1, 3))
        elif line.startswith("### "):
            flow.append(Paragraph(inline(line[4:]), h3))
        elif line.startswith("## "):
            flow.append(Paragraph(inline(line[3:]), h2))
        elif line.startswith("# "):
            flow.append(Paragraph(inline(line[2:]), h1))
        elif line.startswith("> "):
            flow.append(Paragraph(inline(line[2:]), quote))
        elif set(line) <= set("-=* "):
            continue  # разделитель
        else:
            flow.append(Paragraph(inline(line), body))
    if code_lines is not None:  # незакрытый блок — дорисовать как есть
        flow.append(XPreformatted(esc("\n".join(code_lines)), code))
    flush()

    doc = SimpleDocTemplate(
        out, pagesize=A4, leftMargin=22 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=18 * mm, title=title or "MainExperts",
    )
    doc.build(flow)
    print("PDF:", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('usage: pdf_ru.py <draft.md> <out.pdf> ["Заголовок"]', file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        text = f.read()
    build(text, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
