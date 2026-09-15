from __future__ import annotations

from .graph import DynamicHyperGraph
from .schema import TypedHyperEdge


class RuleEngine:
    def infer(self, graph: DynamicHyperGraph) -> int:
        created = 0
        changed = True
        while changed:
            changed = False
            edges = list(graph.find_edges("older_than"))
            for left in edges:
                for right in edges:
                    if left.targets[0] != right.sources[0]:
                        continue
                    src = left.sources[0]
                    dst = right.targets[0]
                    if src == dst:
                        continue
                    edge_id = f"e:{src}:older_than:{dst}"
                    if edge_id in graph.edges:
                        continue
                    confidence = min(left.confidence, right.confidence)
                    graph.add_edge(TypedHyperEdge(
                        id=edge_id,
                        sources=(src,),
                        targets=(dst,),
                        relation="older_than",
                        confidence=confidence,
                        provenance="rule:older_than_transitive",
                    ))
                    created += 1
                    changed = True
        return created
