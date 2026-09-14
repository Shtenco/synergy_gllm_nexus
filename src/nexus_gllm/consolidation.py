from __future__ import annotations

from dataclasses import dataclass
from math import prod

from .graph import DynamicHyperGraph
from .schema import MutationOp


@dataclass(frozen=True)
class ConsolidationReport:
    merged_nodes: int = 0
    merged_edges: int = 0
    retracted_conflicts: int = 0
    semantic_promotions: int = 0
    protected_retained: int = 0
    start_version: int = 0
    end_version: int = 0


class GraphConsolidator:
    EXCLUSIVE_RELATIONS = frozenset({"owned_by", "located_in"})

    @staticmethod
    def _norm_label(label: str) -> str:
        return " ".join(label.casefold().strip().split())

    @staticmethod
    def _replace(values: tuple[str, ...], old: str, new: str) -> tuple[str, ...]:
        return tuple(new if value == old else value for value in values)

    def _merge_duplicate_nodes(self, graph: DynamicHyperGraph) -> int:
        groups: dict[tuple[str, str], list[str]] = {}
        for card in graph.cards.values():
            if card.metadata.get("status") == "merged":
                continue
            key = (card.type.value, self._norm_label(card.label))
            groups.setdefault(key, []).append(card.id)

        merged = 0
        for ids in groups.values():
            if len(ids) < 2:
                continue
            primary = sorted(ids)[0]
            for duplicate in sorted(ids)[1:]:
                dup_card = graph.cards[duplicate]
                dup_card.metadata["merged_into"] = primary
                dup_card.metadata["status"] = "merged"
                dup_card.activation = 0.0
                for edge in graph.edges.values():
                    edge.sources = self._replace(edge.sources, duplicate, primary)
                    edge.targets = self._replace(edge.targets, duplicate, primary)
                graph.cards[primary].consolidation_strength += max(0.1, dup_card.confidence)
                graph._record(MutationOp.MERGE, duplicate, merged_into=primary, source="sleep")
                merged += 1
        return merged

    def _merge_duplicate_edges(self, graph: DynamicHyperGraph) -> tuple[int, int]:
        groups: dict[tuple[str, tuple[str, ...], tuple[str, ...]], list[str]] = {}
        for edge in graph.edges.values():
            if not edge.active:
                continue
            key = (edge.relation, edge.sources, edge.targets)
            groups.setdefault(key, []).append(edge.id)

        merged = 0
        promoted = 0
        for ids in groups.values():
            if len(ids) < 2:
                continue
            primary_id = sorted(ids)[0]
            primary = graph.edges[primary_id]
            evidences = [graph.edges[edge_id].confidence for edge_id in ids]
            primary.confidence = min(1.0, 1.0 - prod(1.0 - float(c) for c in evidences))
            primary.consolidation_strength += float(len(ids) - 1)
            primary.provenance = "sleep:semantic"
            primary.metadata["evidence_edges"] = sorted(ids)
            graph._record(MutationOp.UPDATE, primary_id, source="sleep", confidence=primary.confidence)
            promoted += 1
            for duplicate_id in sorted(ids)[1:]:
                duplicate = graph.edges[duplicate_id]
                duplicate.active = False
                duplicate.metadata["merged_into"] = primary_id
                duplicate.metadata["sleep_merged"] = True
                graph._record(MutationOp.MERGE, duplicate_id, merged_into=primary_id, source="sleep")
                merged += 1
        return merged, promoted

    def _resolve_exclusive_conflicts(self, graph: DynamicHyperGraph) -> int:
        retracted = 0
        for relation in self.EXCLUSIVE_RELATIONS:
            by_source: dict[tuple[str, ...], list[str]] = {}
            for edge in graph.find_edges(relation=relation, active_only=True):
                by_source.setdefault(edge.sources, []).append(edge.id)
            for ids in by_source.values():
                if len(ids) < 2:
                    continue
                ranked = sorted(
                    ids,
                    key=lambda edge_id: (-graph.edges[edge_id].confidence, edge_id),
                )
                keep = ranked[0]
                graph.edges[keep].consolidation_strength += 1.0
                graph._record(MutationOp.UPDATE, keep, source="sleep", exclusive_winner=True)
                for edge_id in ranked[1:]:
                    edge = graph.edges[edge_id]
                    if edge.targets == graph.edges[keep].targets:
                        continue
                    edge.active = False
                    edge.metadata["sleep_retracted"] = True
                    edge.metadata["superseded_by"] = keep
                    graph._record(MutationOp.RETRACT, edge_id, source="sleep", superseded_by=keep)
                    retracted += 1
        return retracted

    def _strengthen_cards(self, graph: DynamicHyperGraph) -> tuple[int, int]:
        promoted = 0
        protected = 0
        for card in graph.cards.values():
            if card.metadata.get("status") == "merged":
                continue
            evidence_count = int(card.metadata.get("evidence_count", 1))
            if evidence_count > 1:
                card.consolidation_strength += float(evidence_count - 1)
                graph._record(MutationOp.UPDATE, card.id, source="sleep", consolidation_strength=card.consolidation_strength)
            if card.metadata.get("protected"):
                protected += 1
            if evidence_count >= 2 and card.provenance not in {"authority", "sleep:semantic"}:
                card.metadata.setdefault("episodic_provenance", card.provenance)
                card.provenance = "sleep:semantic"
                graph._record(MutationOp.UPDATE, card.id, source="sleep", semantic_promotion=True)
                promoted += 1
        return promoted, protected

    def run(self, graph: DynamicHyperGraph) -> ConsolidationReport:
        start_version = graph.version
        merged_nodes = self._merge_duplicate_nodes(graph)
        merged_edges, edge_promotions = self._merge_duplicate_edges(graph)
        retracted_conflicts = self._resolve_exclusive_conflicts(graph)
        card_promotions, protected_retained = self._strengthen_cards(graph)
        return ConsolidationReport(
            merged_nodes=merged_nodes,
            merged_edges=merged_edges,
            retracted_conflicts=retracted_conflicts,
            semantic_promotions=edge_promotions + card_promotions,
            protected_retained=protected_retained,
            start_version=start_version,
            end_version=graph.version,
        )
