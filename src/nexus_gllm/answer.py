from __future__ import annotations

from .compiler_ru import GraphQuery
from .graph import DynamicHyperGraph
from .schema import AnswerGraph


class AnswerResolver:
    def resolve(self, graph: DynamicHyperGraph, query: GraphQuery) -> AnswerGraph:
        edges = graph.find_edges(query.relation)
        if query.intent == "oldest":
            if not edges:
                return AnswerGraph(None, 0.0, "oldest", provenance="abstain")
            sources = {e.sources[0] for e in edges}
            targets = {e.targets[0] for e in edges}
            candidates = sorted(sources - targets)
            if len(candidates) != 1:
                return AnswerGraph(None, 0.0, "oldest", provenance="abstain")
            node_id = candidates[0]
            support = tuple(sorted(e.id for e in edges if e.sources[0] == node_id))
            confidence = min((graph.edges[e].confidence for e in support), default=1.0)
            return AnswerGraph(
                answer_value=graph.cards[node_id].label,
                confidence=confidence,
                intent="oldest",
                support_node_ids=(node_id,),
                support_edge_ids=support,
                provenance="resolver:oldest",
            )

        if query.subject_id is None or query.subject_id not in graph.cards:
            return AnswerGraph(None, 0.0, query.intent, provenance="abstain")
        matches = [e for e in edges if e.sources[0] == query.subject_id]
        if not matches:
            return AnswerGraph(None, 0.0, query.intent, provenance="abstain")
        edge = sorted(matches, key=lambda e: (-e.confidence, e.id))[0]
        target_id = edge.targets[0]
        return AnswerGraph(
            answer_value=graph.cards[target_id].label,
            confidence=edge.confidence,
            intent=query.intent,
            support_node_ids=(query.subject_id, target_id),
            support_edge_ids=(edge.id,),
            provenance="resolver:lookup",
        )
