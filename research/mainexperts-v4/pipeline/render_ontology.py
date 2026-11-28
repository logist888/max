#!/usr/bin/env python3
"""Render the self-contained ontology from its template and registries."""

import argparse
import csv
from collections import Counter
from itertools import groupby
from pathlib import Path

CONFIG = Path(__file__).resolve().parent / 'config'


def read_tsv(name, config):
    with (config / f'{name}.tsv').open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def table(header, rows):
    def row(values):
        return '| ' + ' | '.join(str(x).replace('|', r'\|').replace('\n', ' ') for x in values) + ' |'
    return '\n'.join([row(header), row(['---'] * len(header)), *(row(x) for x in rows)])


def number(x):
    return f'{x:,}'.replace(',', ' ')


def evidence_summary(database, config):
    if database is None:
        return 'Фактические наблюдения сопровождаются сводками базы MainExperts v4.0. Эмпирическая сводка строится при указании аналитической базы.'
    import duckdb

    with duckdb.connect(str(database), read_only=True) as db:
        db.execute('set threads=2')
        source_count, source_rows, nonempty = db.execute("select count(*), sum(rows), sum(query_rows) from sources where status = 'processed'").fetchone()
        query_keys, forms, unknown_market = db.execute('select count(*), count(distinct query_normalized), count(*) filter(where search_market is null) from queries').fetchone()
        rows = [
            ['Прочитано поисковых выгрузок', number(source_count)],
            ['Строк в прочитанных таблицах', number(source_rows)],
            ['Исходных строк с запросом', number(nonempty)],
            ['Уникальных нормализованных формулировок', number(forms)],
            ['Уникальных ключей наблюдаемого спроса', number(query_keys)],
            ['Ключей без установленного рынка поиска', number(unknown_market)],
        ]
        notes = ['Количества отражают обработанные выгрузки. Это не независимая оценка доли рынка, посещений или покупок.']
        known = {name for name, in db.execute('show tables').fetchall()}
        if 'query_labels' not in known:
            return '\n\n'.join([table(['Наблюдение', 'Факт'], rows), *notes,
                'В этом снимке аналитической базы поиск сопоставлений по кластерам ещё не завершён.'])
        n, clusters, semantic, subclusters, candidate_tasks, mapped_queries = db.execute("""
            select count(*), count(distinct cluster_id), count(distinct cluster_base_id),
                   count(distinct subcluster_id), count(distinct task_id),
                   count(*) filter (where task_id is not null)
            from query_labels
        """).fetchone()
        rows += [
            ['Уникальных ключей, прошедших автоматическую разметку', number(n)],
            ['Наблюдаемых кодов семантического семейства', number(semantic)],
            ['Наблюдаемых кодов кластеров намерения', number(clusters)],
            ['Наблюдаемых кодов языково-рыночных подкластеров', number(subclusters)],
            ['Уникальных ключей с автоматической привязкой к листу', number(mapped_queries)],
            ['Различных исходных листьев с автоматической привязкой', f'{candidate_tasks} из 327'],
        ]
        mapped = dict(db.execute('select q_id, count(distinct task_id) from query_labels where task_id is not null group by q_id').fetchall())
        tasks = read_tsv('tasks', config)
        totals = Counter(x['Q_ID'] for x in tasks)
        labels = {x['Q_ID']: x['Q_NAME'] for x in tasks}
        coverage = [[q, labels[q], n, mapped.get(q, 0), n - mapped.get(q, 0)] for q, n in sorted(totals.items())]
        groups = dict(db.execute('select cluster_base_id, count(*) from query_labels where cluster_base_id is not null group by 1').fetchall())
        level_counts = db.execute("select evidence_level, count(*) from query_labels group by 1 order by 1").fetchall()
        intents = dict(db.execute("""
            select cluster_base_id, string_agg(distinct intent_id, ' · ' order by intent_id)
            from query_labels where cluster_base_id is not null group by 1
        """).fetchall())
    notes.append(f'Автоматическая привязка установлена для {mapped_queries / n:.1%} уникальных ключей. Полной классификации корпуса ещё нет. Ручная проверка применимости — самостоятельная задача. Пустое поле оставляет спрос неопределённым.'.replace('.', ',', 1))
    parts = [table(['Наблюдение', 'Факт'], rows), *notes,
        table(['Уровень поискового доказательства', 'Ключей'], [(k or 'Не задан', number(m)) for k, m in level_counts]),
        'D3 описывает кандидатов коммерческого поискового намерения после применения правил и коммерческой перепроверки. Назначение D3 остаётся чувствительным к брендовым, отраслевым и транзакционным омонимам. D4–D6 в корпусе не заявлены.',
        table(['Ветвь', 'Контракт', 'Листьев', 'Связано с запросами', 'Без привязки'], coverage)]
    if (config / 'cluster_catalog.tsv').is_file():
        catalog = read_tsv('cluster_catalog', config)
        parts += ['### Справочник семантических семейств',
                  'Семейство объединяет тематический базовый результат. Его фактические L4-варианты отличаются намерением, L5-варианты — контуром наблюдения. Отдельный нулевой счётчик описывает пустой словарный узел.',
                  table(['Семейство', 'Базовый лист', 'Контракт', 'Обнаруженные намерения L4', 'Ключей'], [
                      [row['CLUSTER_BASE_ID'], row.get('TASK_ID') or '—', row.get('CLUSTER_NAME') or '—', intents.get(row['CLUSTER_BASE_ID']) or '—', number(groups.get(row['CLUSTER_BASE_ID'], 0))]
                      for row in catalog
                  ])]
    return '\n\n'.join(parts)


def build(config, database):
    text = (config / 'ontology_report_template.md').read_text(encoding='utf-8')
    goals = read_tsv('objectives_ontology', config)
    tasks = read_tsv('tasks', config)
    regions = read_tsv('regions_ontology', config)
    boundaries = read_tsv('task_boundaries', config)
    task_groups = {key: list(items) for key, items in groupby(tasks, key=lambda r: r['Q_ID'])}
    appendices = []
    for branch, items in task_groups.items():
        appendices += [f'### {branch} · {items[0]["Q_NAME"]}',
            table(['Код', 'Действие', 'Проверяемый результат'], [
                (f'<span style="white-space:nowrap">{row["TASK_ID"]}</span>', row['TASK_NAME'], row['EXPECTED_RESULT']) for row in items
            ])]
    replacements = {
        'GOALS_TABLE': table(['Код', 'Образовательная цель', 'Завершение', 'Ветви'], [(r['GOAL_ID'], r['OBJECTIVE'], r['RESOLUTION'], r['Q_LINKS'].replace('/', ' · ')) for r in goals]),
        'BRANCH_TABLE': table(['Код', 'Исходная ветвь', 'Листьев'], [(k, g[0]['Q_NAME'], len(g)) for k, g in task_groups.items()]),
        'REGION_TABLE': table(['Система', 'Языки для проверки', 'Локальная граница', 'Проектная страница'], [(r['DESTINATION'], r['LANGUAGES_FOR_COVERAGE'], r['LOCAL_DISTINCTION'], f'`{r["PROJECT_PAGE"]}`') for r in regions]),
        'BOUNDARIES_TABLE': table(['Связанные задачи', 'Что различается', 'Правило'], [(r['TASKS'].replace(' ', ' · '), r['RESOLUTION'], r['ASSIGNMENT_RULE']) for r in boundaries]),
        'EMPIRICAL_SUMMARY': evidence_summary(database, config),
        'TASKS_APPENDIX': '\n\n'.join(appendices),
    }
    for marker, value in replacements.items():
        text = text.replace(f'<!-- {marker} -->', value)
    return text


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', default=CONFIG, type=Path)
    p.add_argument('--db', type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    args.output.write_text(build(args.config, args.db), encoding='utf-8')


if __name__ == '__main__':
    main()
