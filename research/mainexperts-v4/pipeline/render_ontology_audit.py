#!/usr/bin/env python3
"""Turn the independent ontology review and observed regression/holdout counts into Markdown."""
import argparse
import json
from pathlib import Path

from render_ontology import table

NAMES = {'BRANCH_PASS': 'Ветвь', 'TASK_PASS': 'Точный лист', 'EVIDENCE_PASS': 'Потолок доказательности'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def tally(audit):
    return [f'{x["passed"]} / {x["defined"]}' for key in NAMES for x in [audit['scores'][key]]]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--before', required=True, type=Path)
    p.add_argument('--regression', required=True, type=Path)
    p.add_argument('--holdout', required=True, type=Path)
    p.add_argument('--warehouse-audit', type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    before, regression, holdout = map(read, (args.before, args.regression, args.holdout))
    fixture_summary = table(['Набор', *NAMES.values()], [
        ['Исходный независимый контроль', *tally(before)],
        ['Те же формулировки после исправлений', *tally(regression)],
        ['Другие региональные формулировки, после исправлений', *tally(holdout)],
    ])
    failures = []
    for c in holdout['cases']:
        if c['BRANCH_PASS'] and c['TASK_PASS'] is not False and c['EVIDENCE_PASS'] is not False:
            continue
        expected = ' · '.join(filter(None, (c['EXPECTED_Q'], c['EXPECTED_TASK']))) or 'Уточнить'
        observed = ' · '.join(filter(None, (c['ACTUAL_BRANCH'], c['ACTUAL_TASK']))) or 'Сопоставление отсутствует'
        failures.append((c['CASE_ID'], c['QUERY_TEXT'], expected, observed, c['TEST_BOUNDARY']))
    sections = [
        '### Контроль классификации по отдельным формулировкам', fixture_summary,
        'После первого прогона уточнены контракты, распознавание корпусных словоформ и границы соседних результатов. Добавлены отдельные группы для сравнения школьных систем, комплекта материалов на признание, статуса учебного разрешения, записи на день знакомства и сверки кода курса в реестре. Повтор исходного набора служит регрессионной проверкой этих исправлений. Второй набор собран отдельно по региональным процедурам и проверяет переносимость формулировок.',
        'Доказательность здесь проверялась как верхняя граница допустимого уровня для заведомо бесплатных, обязательных внешних или чисто справочных ситуаций. Пустая классификация также проходит проверку верхней границы. Оценка по этому столбцу сама по себе не измеряет полноту обнаружения платного спроса. Оба набора целевые, поэтому эти доли нельзя распространять на весь корпус. Уверенность автоматической разметки отражает эвристику, вероятность корректности на всём массиве пока не откалибрована.',
        '### Открытые расхождения независимого набора',
        table(['ID', 'Формулировка контроля', 'Ожидание', 'Получено', 'Причина контроля'], failures),
        'Кластеры и охват стран следует использовать как прослеживаемые результаты правил разметки. Для решения о запуске нужен ручной просмотр исходных формулировок и применимости по выбранному рынку. Основные направления следующего исправления — многоязычные конструкции вокруг местных процедур, разделение операции возврата и залога, признаки статуса уже начатого дела и ослабление приоритета бренда для конкретной задачи.',
    ]
    if args.warehouse_audit:
        summary = read(args.warehouse_audit)
        sections += [
            '### Сверка аналитической базы',
            table(['Проверка', 'Нарушений'], summary['checks'].items()),
            table(['Результат классификации', 'Ключей', 'Связано с конечным листом'], [
                (x['relevance'], x['total'], x['with_task']) for x in summary['classification_outcomes']
            ]),
        ]
    pth = Path(__file__).resolve().parent / 'config' / 'ontology_audit_template.md'
    base = pth.read_text(encoding='utf-8')
    args.output.write_text(base.replace('<!-- CLASSIFIER_AUDIT -->', '\n\n'.join(sections)), encoding='utf-8')


if __name__ == '__main__':
    main()
