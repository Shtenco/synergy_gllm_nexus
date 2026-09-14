from __future__ import annotations

import json
from pathlib import Path
from .graph import DynamicHyperGraph
from .schema import GraphCard, TypedHyperEdge, NodeType


def save_graph_json(graph: DynamicHyperGraph, path: str | Path) -> None:
    Path(path).write_text(json.dumps(graph.to_dict(), ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")


def load_graph_json(path: str | Path) -> DynamicHyperGraph:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    graph = DynamicHyperGraph()
    for item in data.get("cards", []):
        item["type"] = NodeType(item["type"])
        graph.add_card(GraphCard(**item))
    for item in data.get("edges", []):
        item["sources"] = tuple(item["sources"])
        item["targets"] = tuple(item["targets"])
        graph.add_edge(TypedHyperEdge(**item))
    graph.version = int(data.get("version", graph.version))
    graph.mutation_log.clear()
    return graph
