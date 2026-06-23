#!/usr/bin/env python3
"""Markdown-ish -> PDF с кириллицей (DejaVu Sans).

Использование:
    python3 scripts/pdf_ru.py <draft.md> <out.pdf> ["Заголовок"]

Поддержка: заголовки '# ## ###', списки '- ', цитаты '> ', **жирный**, *курсив*,
пустая строка = разрыв абзаца. Шрифт DejaVu Sans (все доступные начертания);
если нет oblique-файлов — курсив деградирует до прямого (функционально не критично).
"""
import os
import re
import sys

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
)

FONTDIR = "/usr/share/fonts/truetype/dejavu/"


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
registerFontFamily(
    "DejaVu",
    normal="DejaVu",
    bold="DejaVu-Bold",
    italic="DejaVu-Italic",
    boldItalic="DejaVu-BoldItalic",
)


def inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"<i>\1</i>", text)
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
    return body, h1, h2, h3, quote


def build(md: str, out: str, title: str | None = None) -> None:
    body, h1, h2, h3, quote = _styles()
    flow: list = []
    bullets: list = []

    def flush():
        if bullets:
            flow.append(ListFlowable(
                [ListItem(Paragraph(inline(b), body)) for b in bullets],
                bulletType="bullet", start="•",
            ))
            bullets.clear()

    if title:
        flow.append(Paragraph(inline(title), h1))
        flow.append(Spacer(1, 4))

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith(("- ", "* ")):
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
