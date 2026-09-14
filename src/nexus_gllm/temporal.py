from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import hashlib

from .graph import DynamicHyperGraph
from .schema import GraphCard, NodeType, TypedHyperEdge


@dataclass(frozen=True)
class TemporalQueryResult:
    holds: bool
    support_edge_ids: tuple[str, ...] = ()
    confidence: float = 0.0


class EventGraphReasoner:
    def __init__(self, graph: DynamicHyperGraph, strict_dag: bool = True) -> None:
        self.graph = graph
        self.strict_dag = strict_dag

    @staticmethod
    def _norm(text: str) -> str:
        return " ".join(text.strip().split())

    @classmethod
    def _event_id(cls, label: str) -> str:
        norm = cls._norm(label).casefold()
        return "ev_" + hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]

    def ensure_event(
        self,
        label: str,
        *,
        confidence: float = 1.0,
        status: str = "observed",
        sequence_index: int | None = None,
        time_label: str | None = None,
        provenance: str = "event:deterministic",
    ) -> str:
        node_id = self._event_id(label)
        if node_id not in self.graph.cards:
            self.graph.add_card(
                GraphCard(
                    id=node_id,
                    type=NodeType.EVENT,
                    label=self._norm(label),
                    confidence=confidence,
                    provenance=provenance,
                    metadata={
                        "status": status,
                        "sequence_index": sequence_index,
                        "time_label": time_label,
                    },
                )
            )
        return node_id

    def _directed_adjacency(self, relation: str) -> dict[str, list[tuple[str, str, float]]]:
        adjacency: dict[str, list[tuple[str, str, float]]] = {}
        for edge in self.graph.find_edges(relation=relation, active_only=True):
            if len(edge.sources) != 1 or len(edge.targets) != 1:
                continue
            src, dst = edge.sources[0], edge.targets[0]
            adjacency.setdefault(src, []).append((dst, edge.id, edge.confidence))
        return adjacency

    def _path(self, relation: str, source: str, target: str) -> TemporalQueryResult:
        if source == target:
            return TemporalQueryResult(False)
        adjacency = self._directed_adjacency(relation)
        queue = deque([(source, tuple(), 1.0)])
        seen = {source}
        while queue:
            node, support, confidence = queue.popleft()
            for nxt, edge_id, edge_conf in adjacency.get(node, []):
                next_support = (*support, edge_id)
                next_conf = min(confidence, float(edge_conf))
                if nxt == target:
                    return TemporalQueryResult(True, next_support, next_conf)
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, next_support, next_conf))
        return TemporalQueryResult(False)

    def before(self, event_a: str, event_b: str) -> TemporalQueryResult:
        return self._path("before", event_a, event_b)

    def causes(self, event_a: str, event_b: str) -> TemporalQueryResult:
        direct = self._path("causes", event_a, event_b)
        if direct.holds:
            return direct
        return self._path("causal_path", event_a, event_b)

    def _edge_id(self, relation: str, source: str, target: str) -> str:
        return f"e:{source}:{relation}:{target}"

    def _add_relation(
        self,
        relation: str,
        source: str,
        target: str,
        *,
        confidence: float = 1.0,
        provenance: str = "event:deterministic",
        dag_relation: str | None = None,
    ) -> str:
        if source not in self.graph.cards or target not in self.graph.cards:
            raise ValueError("event relation references unknown node")
        if source == target:
            raise ValueError(f"{relation} cycle/self-loop rejected")
        check_relation = dag_relation or relation
        if self.strict_dag and self._path(check_relation, target, source).holds:
            raise ValueError(f"{relation} cycle rejected")
        edge_id = self._edge_id(relation, source, target)
        existing = self.graph.edges.get(edge_id)
        if existing is not None:
            if not existing.active:
                existing.active = True
            existing.confidence = max(existing.confidence, confidence)
            return edge_id
        self.graph.add_edge(
            TypedHyperEdge(
                id=edge_id,
                sources=(source,),
                targets=(target,),
                relation=relation,
                confidence=confidence,
                provenance=provenance,
            )
        )
        return edge_id

    def add_before(self, event_a: str, event_b: str, *, confidence: float = 1.0) -> str:
        return self._add_relation("before", event_a, event_b, confidence=confidence)

    def add_after(self, event_a: str, event_b: str, *, confidence: float = 1.0) -> str:
        # A after B is stored canonically as B before A.
        return self.add_before(event_b, event_a, confidence=confidence)

    def add_cause(self, cause: str, effect: str, *, confidence: float = 1.0) -> str:
        return self._add_relation("causes", cause, effect, confidence=confidence)

    def add_actor(self, event: str, entity: str, *, confidence: float = 1.0) -> str:
        return self._add_relation("actor", event, entity, confidence=confidence)

    def add_object(self, event: str, entity: str, *, confidence: float = 1.0) -> str:
        return self._add_relation("object", event, entity, confidence=confidence)

    def materialize_closure(self) -> tuple[str, ...]:
        """Materialize safe derived temporal/causal closure edges for inspection/training."""
        created: list[str] = []
        event_ids = [card.id for card in self.graph.cards.values() if card.type == NodeType.EVENT]
        for source in event_ids:
            for target in event_ids:
                if source == target:
                    continue
                temporal = self._path("before", source, target)
                edge_id = self._edge_id("before", source, target)
                if temporal.holds and edge_id not in self.graph.edges and len(temporal.support_edge_ids) > 1:
                    self.graph.add_edge(
                        TypedHyperEdge(
                            id=edge_id,
                            sources=(source,),
                            targets=(target,),
                            relation="before",
                            confidence=temporal.confidence,
                            provenance="rule:temporal_transitive",
                        )
                    )
                    created.append(edge_id)
                causal = self._path("causes", source, target)
                cedge_id = self._edge_id("causal_path", source, target)
                if causal.holds and cedge_id not in self.graph.edges and len(causal.support_edge_ids) > 1:
                    self.graph.add_edge(
                        TypedHyperEdge(
                            id=cedge_id,
                            sources=(source,),
                            targets=(target,),
                            relation="causal_path",
                            confidence=causal.confidence,
                            provenance="rule:causal_ancestry",
                        )
                    )
                    created.append(cedge_id)
        return tuple(created)
