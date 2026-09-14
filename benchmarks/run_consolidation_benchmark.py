from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexus_gllm.consolidation import GraphConsolidator
from nexus_gllm.graph import DynamicHyperGraph
from nexus_gllm.schema import GraphCard, NodeType, TypedHyperEdge


def run_consolidation_smoke() -> dict:
    cases: list[tuple[str, bool]] = []

    graph = DynamicHyperGraph()
    graph.add_card(GraphCard(id="p1", type=NodeType.PERSON, label="Антон"))
    graph.add_card(GraphCard(id="p2", type=NodeType.PERSON, label=" антон "))
    graph.add_card(GraphCard(id="car", type=NodeType.ENTITY, label="Автомобиль"))
    graph.add_card(GraphCard(id="b", type=NodeType.PERSON, label="Борис"))
    graph.add_edge(TypedHyperEdge(id="dup1", sources=("car",), targets=("p2",), relation="owned_by", confidence=0.6))
    graph.add_edge(TypedHyperEdge(id="best", sources=("car",), targets=("b",), relation="owned_by", confidence=0.95))
    report = GraphConsolidator().run(graph)
    cases.append(("duplicate_node_retained", "p2" in graph.cards and graph.cards["p2"].metadata.get("status") == "merged"))
    cases.append(("rewire_after_merge", graph.edges["dup1"].targets == ("p1",)))
    cases.append(("exclusive_conflict_resolved", graph.edges["best"].active and not graph.edges["dup1"].active))
    cases.append(("report_conflict", report.retracted_conflicts == 1))

    evidence = DynamicHyperGraph()
    evidence.add_card(GraphCard(id="x", type=NodeType.ENTITY, label="X"))
    evidence.add_card(GraphCard(id="y", type=NodeType.CONCEPT, label="Y"))
    evidence.add_edge(TypedHyperEdge(id="e1", sources=("x",), targets=("y",), relation="is_a", confidence=0.6))
    evidence.add_edge(TypedHyperEdge(id="e2", sources=("x",), targets=("y",), relation="is_a", confidence=0.5))
    GraphConsolidator().run(evidence)
    active = evidence.find_edges("is_a")
    cases.append(("confidence_accumulation", len(active) == 1 and abs(active[0].confidence - 0.8) < 1e-9))

    passed = sum(1 for _, ok in cases if ok)
    return {
        "total": len(cases),
        "passed": passed,
        "accuracy": passed / len(cases) if cases else 0.0,
        "cases": [{"name": name, "passed": bool(ok)} for name, ok in cases],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run_consolidation_smoke()
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
