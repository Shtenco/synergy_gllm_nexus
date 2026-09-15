from __future__ import annotations

from dataclasses import dataclass
from .graph import DynamicHyperGraph
from .schema import TypedHyperEdge


@dataclass(frozen=True)
class StructuralProposal:
    op: str
    confidence: float
    source_id: str | None = None
    target_id: str | None = None
    relation: str | None = None
    edge_id: str | None = None


@dataclass(frozen=True)
class MutationResult:
    applied: bool
    reason: str
    edge_id: str | None = None


class MutationPolicy:
    """Validates neural structural proposals before persistent graph mutation."""

    def __init__(self, threshold: float = 0.8) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be within [0,1]")
        self.threshold = threshold

    def apply(self, graph: DynamicHyperGraph, proposal: StructuralProposal) -> MutationResult:
        if not 0.0 <= proposal.confidence <= 1.0:
            return MutationResult(False, "invalid_confidence")
        if proposal.confidence < self.threshold:
            return MutationResult(False, "below_threshold")

        op = proposal.op.upper()
        if op == "LINK":
            if not proposal.source_id or not proposal.target_id or not proposal.relation:
                return MutationResult(False, "missing_link_fields")
            if proposal.source_id not in graph.cards or proposal.target_id not in graph.cards:
                return MutationResult(False, "unknown_node")
            edge_id = proposal.edge_id or f"n:{proposal.source_id}:{proposal.relation}:{proposal.target_id}"
            if edge_id in graph.edges:
                return MutationResult(False, "edge_exists", edge_id=edge_id)
            graph.add_edge(TypedHyperEdge(
                id=edge_id,
                sources=(proposal.source_id,),
                targets=(proposal.target_id,),
                relation=proposal.relation,
                confidence=proposal.confidence,
                provenance="neural:validated_proposal",
            ))
            return MutationResult(True, "linked", edge_id=edge_id)

        if op == "RETRACT":
            if not proposal.edge_id or proposal.edge_id not in graph.edges:
                return MutationResult(False, "unknown_edge", edge_id=proposal.edge_id)
            if not graph.edges[proposal.edge_id].active:
                return MutationResult(False, "already_inactive", edge_id=proposal.edge_id)
            graph.retract_edge(proposal.edge_id)
            return MutationResult(True, "retracted", edge_id=proposal.edge_id)

        if op in {"ACTIVATE", "SUPPRESS"}:
            target_id = proposal.source_id or proposal.target_id
            if not target_id or target_id not in graph.cards:
                return MutationResult(False, "unknown_node")
            graph.cards[target_id].activation = 1.0 if op == "ACTIVATE" else 0.0
            return MutationResult(True, op.lower())

        return MutationResult(False, "unsupported_operation")
