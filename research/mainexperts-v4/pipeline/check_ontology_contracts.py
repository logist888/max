#!/usr/bin/env python3
"""Check baseline references and an independent boundary fixture set.

Fixtures are analytical controls. They are not evidence of query demand.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent


def read_tsv(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def read_config(name, config):
    return read_tsv(config / f'{name}.tsv')


def structure(config):
    tasks = read_config('tasks', config)
    goals = read_config('objectives_ontology', config)
    regions = read_config('regions_ontology', config)
    documents = read_config('regional_documents', config)
    benchmarks = read_config('ontology_fixtures', config)
    branches = Counter(task['Q_ID'] for task in tasks)
    codes = {task['TASK_ID'] for task in tasks}
    checks = {
        'baseline has 327 unique tasks and 22 branches': len(codes) == len(tasks) == 327 and len(branches) == 22,
        'branch derived from each task ID matches its primary branch': all(x['TASK_ID'].partition('.')[0] == x['Q_ID'] for x in tasks),
        'each task has an action, result and source locator': all(x['TASK_NAME'] and x['EXPECTED_RESULT'] and x['SOURCE_LOCATOR'] for x in tasks),
        'all branches are linked to educational goals': set.union(*(set(x['Q_LINKS'].split('/')) for x in goals)) == set(branches),
        'all 14 region contexts refer to read source documents': len({x['DESTINATION'] for x in regions}) == 14 and all(
            x['ONTOLOGY_DRIVE_INDEX'] in {x['DRIVE_INDEX'] for x in documents if x['READ_STATUS'] == 'read_text'} for x in regions
        ),
        'all independently defined fixture leaves resolve': all(not x['EXPECTED_TASK'] or x['EXPECTED_TASK'] in codes for x in benchmarks),
        'fixtures include all 22 branches': set.union(*(set(x['EXPECTED_Q'].split('/')) for x in benchmarks)) - {''} == set(branches),
    }
    return checks, branches, benchmarks


def classifier_result(benchmarks):
    from classify import classify

    cases = []
    for case in benchmarks:
        raw = case['QUERY_TEXT']
        result = classify(raw, '', case['SEARCH_MARKET'] or None)
        branch = result.get('Q_ID') or ''
        leaf = result.get('TASK_ID') or ''
        evidence = result.get('EVIDENCE_LEVEL') or 'D0'
        expected = case['EXPECTED_Q'].split('/')
        case.update({
            'ACTUAL_BRANCH': branch, 'BRANCH_PASS': branch in expected,
            'ACTUAL_TASK': leaf, 'TASK_PASS': None if not case['EXPECTED_TASK'] else leaf == case['EXPECTED_TASK'],
            'ACTUAL_INTENT': result.get('INTENT_ID'), 'ACTUAL_EVIDENCE': evidence,
            'EVIDENCE_PASS': None if not case['MAX_EVIDENCE'] else evidence <= case['MAX_EVIDENCE'],
            'ACTUAL_CLUSTER': result.get('CLUSTER_ID'), 'ACTUAL_DESTINATION': result.get('DESTINATION_HINT'),
        })
        cases.append(case)
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=BASE / 'config')
    parser.add_argument('--run-classifier', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--fixtures', type=Path, help='Use a separate classifier control set')
    args = parser.parse_args()
    checks, branches, benchmarks = structure(args.config)
    if args.fixtures:
        benchmarks = read_tsv(args.fixtures)
    result = {'structure': checks, 'branches': dict(branches), 'fixture_count': len(benchmarks)}
    if args.run_classifier:
        result['cases'] = classifier_result(benchmarks)
        result['scores'] = {
            k: {'passed': sum(x[k] is True for x in result['cases']), 'defined': sum(x[k] is not None for x in result['cases'])}
            for k in ['BRANCH_PASS', 'TASK_PASS', 'EVIDENCE_PASS']
        }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered, encoding='utf-8')
    else:
        print(rendered, end='')
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
