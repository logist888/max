#!/usr/bin/env python3
"""Независимый контролёр графа. Пересчитывает узлы/связи/провенанс из
build/graph/*.jsonl и сверяет с report.json конвейера. Расхождение выводов
двух независимых счётчиков — само по себе повод для разбирательства
(та же дисциплина, что pipeline/contract.ts ↔ audit_json.py).

Запуск: python3 seo-platform/graph_audit.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

BUILD = Path(__file__).parent / "app" / "build" / "graph"


def load_jsonl(path: Path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def main() -> int:
    nodes = load_jsonl(BUILD / "nodes.jsonl")
    edges = load_jsonl(BUILD / "edges.jsonl")
    report_path = BUILD / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}

    node_ids = {n["id"] for n in nodes}
    by_node = Counter(n["type"] for n in nodes)
    by_edge = Counter(e["type"] for e in edges)

    problems = []
    # висячие связи
    dangling = [e["id"] for e in edges if e["from"] not in node_ids or e["to"] not in node_ids]
    if dangling:
        problems.append(f"висячих связей: {len(dangling)} (напр. {dangling[:3]})")
    # дубли id
    if len(node_ids) != len(nodes):
        problems.append(f"дубли id узлов: {len(nodes) - len(node_ids)}")
    # факт без провенанса
    fact_no_prov = sum(1 for n in nodes if n.get("status") == "факт" and not n.get("provenance"))
    fact_no_prov += sum(1 for e in edges if e.get("status") == "факт" and not e.get("provenance"))
    if fact_no_prov:
        problems.append(f"факт без provenance: {fact_no_prov}")
    # выводимое как факт
    bad_inferred = sum(1 for e in edges if e.get("method") in ("inferred", "curated") and e.get("status") == "факт")
    if bad_inferred:
        problems.append(f"inferred/curated со status=факт: {bad_inferred}")

    # сверка счётчиков с report.json конвейера
    mism = []
    if report:
        if report.get("nodes") != len(nodes):
            mism.append(f"nodes: report={report.get('nodes')} audit={len(nodes)}")
        if report.get("edges") != len(edges):
            mism.append(f"edges: report={report.get('edges')} audit={len(edges)}")

    print(f"[graph_audit] узлов {len(nodes)}, связей {len(edges)}")
    print(f"[graph_audit] по типам узлов: {dict(by_node)}")
    print(f"[graph_audit] по типам связей: {dict(by_edge)}")
    if mism:
        print("[graph_audit] РАСХОЖДЕНИЕ с report.json: " + "; ".join(mism))
    if problems:
        print("[graph_audit] проблемы: " + "; ".join(problems))
        return 1
    if mism:
        return 1
    print("[graph_audit] сверка пройдена: зелено")
    return 0


if __name__ == "__main__":
    sys.exit(main())
