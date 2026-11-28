#!/usr/bin/env python3
"""Extract and validate the canonical MainExperts v2 task register."""

import argparse
import csv
import re
import subprocess
from pathlib import Path

FIELDS = (
    'TASK_ID', 'Q_ID', 'Q_NAME', 'TASK_GROUP', 'TASK_NAME', 'EXPECTED_RESULT', 'SOURCE_LOCATOR',
)
ROW = re.compile(r'\| (Q\d{2}\.\d{2}[a-z]?) \| (.+?) \| (.+?) \|\s*$')
BRANCH = re.compile(r'## (Q\d{2}) · (.+)')
PDF_ID = re.compile(r'^\s+(Q\d{2}\.\d{2}[a-z]?)\s', flags=re.M)


def extract(markdown):
    section = markdown.split('# 5. Дерево вопросов', 1)[1]
    section = section.split('# 6. Состояния и переходы', 1)[0]
    branch = branch_name = group = None
    rows = []
    for line in section.splitlines():
        if branch_match := BRANCH.fullmatch(line):
            branch, branch_name = branch_match.groups()
            group = None
        if line.startswith('### '):
            group = line[4:]
        if match := ROW.fullmatch(line):
            task_id, task, result = match.groups()
            if not group or task_id.partition('.')[0] != branch:
                raise ValueError(f'Task outside its declared branch or group: {task_id}')
            rows.append((task_id, branch, branch_name, group, task, result, 'global-ontology-v2-tables §5'))
    ids = [row[0] for row in rows]
    branches = {row[1] for row in rows}
    if len(ids) != 327 or len(set(ids)) != 327 or len(branches) != 22:
        raise ValueError('Unexpected edition or incomplete task extract (expected 327 unique tasks, 22 branches)')
    return rows


def check_pdf(pdf_path, rows):
    pdf = subprocess.run(
        ['pdftotext', '-f', '26', '-l', '52', '-layout', str(pdf_path), '-'],
        capture_output=True, check=True, text=True,
    ).stdout
    ids = PDF_ID.findall(pdf)
    if ids != [row[0] for row in rows]:
        raise ValueError('Ordered task IDs differ between PDF pages 26–52 and Markdown section 5')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--markdown', required=True, type=Path)
    parser.add_argument('--pdf', type=Path, help='Check the independent PDF extraction with Poppler')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    rows = extract(args.markdown.read_text(encoding='utf-8'))
    if args.pdf:
        check_pdf(args.pdf, rows)
    with args.output.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        writer.writerow(FIELDS)
        writer.writerows(rows)
    print(f'{len(rows)} tasks, {len({row[1] for row in rows})} branches, PDF check={bool(args.pdf)}')


if __name__ == '__main__':
    main()
