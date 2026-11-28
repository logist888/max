"""Write the audited workbook using constant memory for the full query sheet."""
import argparse
import json
from pathlib import Path

import xlsxwriter

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('config', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
config = json.loads(args.config.read_text(encoding='utf-8'))

with xlsxwriter.Workbook(args.output, {
    'constant_memory': True,
    'strings_to_formulas': False,
    'strings_to_urls': False,
}) as workbook:
    base = {'font_name': 'Golos Text', 'font_size': 10, 'valign': 'vcenter'}
    heading = workbook.add_format(base | {
        'bg_color': '#123457', 'font_color': '#FFFFFF', 'bold': True, 'font_size': 15,
    })
    note = workbook.add_format(base | {
        'bg_color': '#E8F1F9', 'font_color': '#173451', 'text_wrap': True,
    })
    header = workbook.add_format(base | {
        'bg_color': '#205888', 'font_color': '#FFFFFF', 'bold': True, 'text_wrap': True,
    })
    for tab in config:
        sheet = workbook.add_worksheet(tab['name'])
        sheet.hide_gridlines(2)
        sheet.set_tab_color('#123457' if tab['name'] == 'Сводка' else '#205888')
        last_column = len(tab['headers']) - 1
        for column, width in enumerate(tab['widths'] or [150] * (last_column + 1)):
            sheet.set_column_pixels(column, column, width)
        sheet.set_row(0, 35)
        sheet.merge_range(0, 0, 0, last_column, tab['title'], heading)
        sheet.set_row(1, 31)
        sheet.merge_range(1, 0, 1, last_column, tab['description'], note)
        sheet.set_row(3, 25)
        sheet.write_row(3, 0, tab['headers'], header)
        sheet.freeze_panes(4, 0)
        sheet.autofilter(3, 0, len(tab['rows']) + 3, last_column)

        style = {'font_color': '#173451', 'text_wrap': len(tab['rows']) < 6_500}
        fills = ('#F2F7FC', '#FFFFFF')
        body = [workbook.add_format(base | style | {'bg_color': color}) for color in fills]
        for row_number, row in enumerate(tab['rows'], start=4):
            if tab['rowHeight'] and len(tab['rows']) < 6_500:
                sheet.set_row(row_number, tab['rowHeight'])
            values = [None if value == '' else value for value in row]
            sheet.write_row(row_number, 0, values, body[row_number % 2])
        print(tab['name'], len(tab['rows']))
