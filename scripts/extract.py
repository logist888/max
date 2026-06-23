#!/usr/bin/env python3
"""Локальный файл -> текст. Fallback: основной путь ингеста — Drive MCP.

Использование:
    python3 scripts/extract.py <файл>

PDF -> pypdf (постранично, с маркерами страниц); txt/md -> как есть;
docx -> python-docx (если установлен).
"""
import os
import sys


def from_pdf(path: str) -> str:
    from pypdf import PdfReader
    reader = PdfReader(path)
    parts = []
    for i, page in enumerate(reader.pages, 1):
        parts.append(f"\n\n===== стр. {i} =====\n" + (page.extract_text() or ""))
    return "".join(parts)


def from_docx(path: str) -> str:
    import docx
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: extract.py <файл>", file=sys.stderr)
        sys.exit(2)
    path = sys.argv[1]
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        print(from_pdf(path))
    elif ext in (".txt", ".md"):
        with open(path, encoding="utf-8") as f:
            print(f.read())
    elif ext == ".docx":
        print(from_docx(path))
    else:
        print(f"неподдерживаемый тип: {ext}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
