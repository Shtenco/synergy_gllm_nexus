from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .graph import DynamicHyperGraph
from .schema import GraphCard, TypedHyperEdge, NodeType


@dataclass(frozen=True)
class GraphQuery:
    relation: str
    subject_id: str | None = None
    intent: str = "lookup"


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
