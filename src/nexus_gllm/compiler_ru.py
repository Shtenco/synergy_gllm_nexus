from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .graph import DynamicHyperGraph
from .schema import GraphCard, TypedHyperEdge, NodeType
from .temporal import EventGraphReasoner


@dataclass(frozen=True)
class GraphQuery:
    relation: str
    subject_id: str | None = None
    intent: str = "lookup"


@dataclass(frozen=True)
class EventGraphQuery:
    kind: str
    left: str | None = None
    right: str | None = None
    target: str | None = None


def _stable_id(label: str) -> str:
    digest = hashlib.sha1(label.casefold().encode("utf-8")).hexdigest()[:10]
    return f"n_{digest}"


def _canonical_name(name: str) -> str:
    name = name.strip(" .,!?:;\"'()")
    low = name.casefold()
    # Minimal transparent morphology for common masculine Russian proper names.
    if low.endswith(("иса", "ора", "она", "тра")) and len(name) > 4:
        name = name[:-1]
        low = name.casefold()
    if low.endswith(("ону", "ису", "ору", "тру")) and len(name) > 4:
        name = name[:-1]
    return name


class RussianGraphCompiler:
    _patterns = (
        (re.compile(r"^(.+?)\s+старше\s+(.+?)\.?$", re.I), "older_than", NodeType.PERSON, NodeType.PERSON),
        (re.compile(r"^(.+?)\s+находится\s+в\s+(.+?)\.?$", re.I), "located_in", NodeType.ENTITY, NodeType.PLACE),
        (re.compile(r"^(.+?)\s+принадлежит\s+(.+?)\.?$", re.I), "owned_by", NodeType.ENTITY, NodeType.PERSON),
        (re.compile(r"^(.+?)\s+(?:—\s*)?(?:это|является)\s+(.+?)\.?$", re.I), "is_a", NodeType.ENTITY, NodeType.CONCEPT),
    )
    _exclusive_relations = {"owned_by", "located_in"}

    _first_then = re.compile(r"^Сначала\s+(.+?),\s*потом\s+(.+?)\.?$", re.I)
    _therefore = re.compile(r"^(.+?),\s*поэтому\s+(.+?)\.?$", re.I)
    _after = re.compile(r"^После\s+(.+?)\s+произошл[оаи]\s+(.+?)\.?$", re.I)
    _temporal_question = re.compile(r"^Что было раньше:\s*(.+?)\s+или\s+(.+?)\??$", re.I)
    _cause_question = re.compile(r"^Что стало причиной\s+(.+?)\??$", re.I)

    def _ensure(self, graph: DynamicHyperGraph, label: str, type_: NodeType) -> str:
        label = _canonical_name(label)
        node_id = _stable_id(label)
        if node_id not in graph.cards:
            graph.add_card(GraphCard(id=node_id, type=type_, label=label, provenance="compiler:ru:v1"))
        return node_id

    def compile_statement(self, text: str, graph: DynamicHyperGraph):
        clean = " ".join(text.strip().split())
        for pattern, relation, src_type, dst_type in self._patterns:
            m = pattern.match(clean)
            if not m:
                continue
            src = self._ensure(graph, m.group(1), src_type)
            dst = self._ensure(graph, m.group(2), dst_type)
            edge_id = f"e:{src}:{relation}:{dst}"

            if relation in self._exclusive_relations:
                for edge in list(graph.find_edges(relation)):
                    if edge.sources == (src,) and edge.targets != (dst,):
                        graph.retract_edge(edge.id)

            existing = graph.edges.get(edge_id)
            if existing is not None:
                if not existing.active:
                    existing.active = True
                return None

            return graph.add_edge(TypedHyperEdge(
                id=edge_id,
                sources=(src,),
                targets=(dst,),
                relation=relation,
                confidence=1.0,
                provenance="compiler:ru:v1",
            ))
        raise ValueError(f"unsupported Russian statement: {text}")

    def compile_question(self, text: str, graph: DynamicHyperGraph) -> GraphQuery:
        clean = " ".join(text.strip().split()).rstrip("?.!")
        low = clean.casefold()
        if low in {"кто самый старший", "кто старше"}:
            return GraphQuery("older_than", intent="oldest")
        m = re.match(r"^где находится (.+)$", clean, re.I)
        if m:
            return GraphQuery("located_in", _stable_id(_canonical_name(m.group(1))), "location")
        m = re.match(r"^кому принадлежит (.+)$", clean, re.I)
        if m:
            return GraphQuery("owned_by", _stable_id(_canonical_name(m.group(1))), "ownership")
        raise ValueError(f"unsupported Russian question: {text}")

    @staticmethod
    def _clean_event_label(text: str) -> str:
        return " ".join(text.strip(" .,!?:;\"'() ").split())

    def compile_event_statement(self, text: str, graph: DynamicHyperGraph) -> dict:
        clean = " ".join(text.strip().split())
        temporal = EventGraphReasoner(graph)

        match = self._first_then.match(clean)
        if match:
            left = self._clean_event_label(match.group(1))
            right = self._clean_event_label(match.group(2))
            left_id = temporal.ensure_event(left, sequence_index=0, provenance="compiler:ru:event:v1")
            right_id = temporal.ensure_event(right, sequence_index=1, provenance="compiler:ru:event:v1")
            edge_id = temporal.add_before(left_id, right_id)
            return {"relation": "before", "source": left_id, "target": right_id, "edge_id": edge_id}

        match = self._therefore.match(clean)
        if match:
            cause = self._clean_event_label(match.group(1))
            effect = self._clean_event_label(match.group(2))
            cause_id = temporal.ensure_event(cause, provenance="compiler:ru:event:v1")
            effect_id = temporal.ensure_event(effect, provenance="compiler:ru:event:v1")
            edge_id = temporal.add_cause(cause_id, effect_id)
            return {"relation": "causes", "source": cause_id, "target": effect_id, "edge_id": edge_id}

        match = self._after.match(clean)
        if match:
            earlier = self._clean_event_label(match.group(1))
            later = self._clean_event_label(match.group(2))
            earlier_id = temporal.ensure_event(earlier, sequence_index=0, provenance="compiler:ru:event:v1")
            later_id = temporal.ensure_event(later, sequence_index=1, provenance="compiler:ru:event:v1")
            edge_id = temporal.add_before(earlier_id, later_id)
            return {"relation": "before", "source": earlier_id, "target": later_id, "edge_id": edge_id}

        raise ValueError(f"unsupported Russian event statement: {text}")

    def compile_event_question(self, text: str) -> EventGraphQuery:
        clean = " ".join(text.strip().split())
        match = self._temporal_question.match(clean)
        if match:
            return EventGraphQuery(
                kind="temporal_choice",
                left=self._clean_event_label(match.group(1)),
                right=self._clean_event_label(match.group(2)),
            )
        match = self._cause_question.match(clean)
        if match:
            return EventGraphQuery(
                kind="cause_of",
                target=self._clean_event_label(match.group(1)),
            )
        raise ValueError(f"unsupported Russian event question: {text}")
