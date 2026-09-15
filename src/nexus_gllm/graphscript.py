from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class GraphScriptNode:
    id: str
    type: str
    label: str | None = None


@dataclass(frozen=True)
class GraphScriptEdge:
    source: str
    target: str
    relation: str
    confidence: float = 1.0


@dataclass(frozen=True)
class GraphScriptDocument:
    nodes: tuple[GraphScriptNode, ...]
    edges: tuple[GraphScriptEdge, ...]
    query: str | None = None
    answer: str | None = None


_NODE = re.compile(r'^NODE\s+([A-Za-z0-9_.:-]+)\s*:\s*([A-Z_]+)(?:\s+\["(.*)"\])?$')
_EDGE = re.compile(r'^EDGE\s+([A-Za-z0-9_.:-]+)\s*->\s*([A-Za-z0-9_.:-]+)\s*:\s*([A-Za-z0-9_.:-]+)(?:\s+CONF=([0-9.]+))?$')
_QUERY = re.compile(r'^QUERY\s+(.+)$')
_ANSWER = re.compile(r'^ANSWER\s+(.+)$')


def parse_graphscript(text: str) -> GraphScriptDocument:
    nodes: list[GraphScriptNode] = []
    edges: list[GraphScriptEdge] = []
    query = None
    answer = None
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        m = _NODE.match(line)
        if m:
            nodes.append(GraphScriptNode(m.group(1), m.group(2), m.group(3)))
            continue
        m = _EDGE.match(line)
        if m:
            conf = float(m.group(4)) if m.group(4) else 1.0
            if not 0.0 <= conf <= 1.0:
                raise ValueError(f"line {line_no}: confidence outside [0,1]")
            edges.append(GraphScriptEdge(m.group(1), m.group(2), m.group(3), conf))
            continue
        m = _QUERY.match(line)
        if m:
            query = m.group(1)
            continue
        m = _ANSWER.match(line)
        if m:
            answer = m.group(1)
            continue
        raise ValueError(f"line {line_no}: invalid GraphScript: {line}")
    return GraphScriptDocument(tuple(nodes), tuple(edges), query, answer)


def format_graphscript(doc: GraphScriptDocument) -> str:
    lines: list[str] = []
    for node in doc.nodes:
        suffix = f' ["{node.label}"]' if node.label is not None else ''
        lines.append(f"NODE {node.id} : {node.type}{suffix}")
    for edge in doc.edges:
        lines.append(f"EDGE {edge.source} -> {edge.target} : {edge.relation} CONF={edge.confidence:.1f}")
    if doc.query is not None:
        lines.append(f"QUERY {doc.query}")
    if doc.answer is not None:
        lines.append(f"ANSWER {doc.answer}")
    return "\n".join(lines)
