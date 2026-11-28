#!/usr/bin/env python3
"""Audit cross-table ontology integrity without mutating the analytical warehouse."""
import argparse
import json
from pathlib import Path

import duckdb


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    with duckdb.connect(str(args.db), read_only=True) as db:
        db.execute('set threads=2')
        checks = {
            'orphan_task_labels': '''select count(*) from query_labels l left join tasks t
                using(task_id) where l.task_id is not null and t.task_id is null''',
            'mislabeled_task_branch': '''select count(*) from query_labels l join tasks t
                using(task_id) where l.q_id is distinct from t.q_id''',
            'unknown_cluster_families': '''select count(*) from query_labels l left join cluster_catalog c
                using(cluster_base_id) where l.cluster_base_id is not null and c.cluster_base_id is null''',
            'incompatible_l4_labels': '''select count(*) from query_labels where cluster_id is not null
                and cluster_id is distinct from cluster_base_id || '-' || intent_id''',
            'incompatible_l5_labels': '''select count(*) from query_labels l join queries q using(query_id)
                where subcluster_id is not null and subcluster_id is distinct from
                cluster_id || ':' || coalesce(q.search_market,'und') || ':' || coalesce(l.language,'und')''',
            'analysis_labels_above_search_only_level': '''select count(*) from query_labels where evidence_level in ('D4','D5','D6')''',
            'commercial_labels_without_service': '''select count(*) from query_labels where evidence_level='D3' and service_id is null''',
        }
        issues = {name: db.execute(sql).fetchone()[0] for name, sql in checks.items()}
        distinct, records, navigational_count = db.execute(\
            "select count(distinct query_id), count(*), count(*) filter(where relevance='navigation') from query_labels"\
        ).fetchone()
        assignment = db.execute('''select relevance, count(*) n, count(*) filter(where task_id is not null) task_mapped
            from query_labels group by 1 order by n desc''').fetchall()
        stats = {
            'checks': issues,
            'classified_rows': records,
            'distinct_classified_keys': distinct,
            'navigational_keys': navigational_count,
            'classification_outcomes': [dict(relevance=r, total=n, with_task=t) for r,n,t in assignment],
        }
    args.output.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if any(issues.values()) or records != distinct:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
