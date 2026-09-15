from __future__ import annotations

from dataclasses import asdict
from .schema import GraphCard, TypedHyperEdge, GraphUpdate, MutationOp


class DynamicHyperGraph:
    def __init__(self) -> None:
        self.cards: dict[str, GraphCard] = {}
        self.edges: dict[str, TypedHyperEdge] = {}
        self.version = 0
        self.mutation_log: list[GraphUpdate] = []

    def _record(self, op: MutationOp, target_id: str, **detail) -> GraphUpdate:
        self.version += 1
        update = GraphUpdate(op=op, target_id=target_id, graph_version=self.version, detail=detail)
        self.mutation_log.append(update)
        return update

    def add_card(self, card: GraphCard) -> GraphUpdate:
        if card.id in self.cards:
            raise ValueError(f"duplicate card id: {card.id}")
        self.cards[card.id] = card
        return self._record(MutationOp.CREATE, card.id)

    def upsert_card(self, card: GraphCard) -> GraphUpdate:
        if card.id in self.cards:
            self.cards[card.id] = card
            return self._record(MutationOp.UPDATE, card.id)
        return self.add_card(card)

    def add_edge(self, edge: TypedHyperEdge) -> GraphUpdate:
        if edge.id in self.edges:
            raise ValueError(f"duplicate edge id: {edge.id}")
        missing = [n for n in edge.sources + edge.targets if n not in self.cards]
        if missing:
            raise ValueError(f"edge references unknown nodes: {missing}")
        self.edges[edge.id] = edge
        return self._record(MutationOp.LINK, edge.id)

    def find_edges(self, relation: str | None = None, active_only: bool = True) -> list[TypedHyperEdge]:
        values = list(self.edges.values())
        if relation is not None:
            values = [e for e in values if e.relation == relation]
        if active_only:
            values = [e for e in values if e.active]
        return values

    def retract_edge(self, edge_id: str) -> GraphUpdate:
        edge = self.edges[edge_id]
        edge.active = False
        return self._record(MutationOp.RETRACT, edge_id)

    def neighbors(self, node_id: str) -> set[str]:
        out: set[str] = set()
        for edge in self.find_edges():
            members = set(edge.sources + edge.targets)
            if node_id in members:
                out.update(members)
        out.discard(node_id)
        return out

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "cards": [asdict(self.cards[k]) for k in sorted(self.cards)],
            "edges": [asdict(self.edges[k]) for k in sorted(self.edges)],
        }
