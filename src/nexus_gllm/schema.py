from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    ENTITY = "ENTITY"
    EVENT = "EVENT"
    ACTION = "ACTION"
    PROPERTY = "PROPERTY"
    RELATION = "RELATION"
    CLAIM = "CLAIM"
    QUESTION = "QUESTION"
    GOAL = "GOAL"
    RULE = "RULE"
    CAUSE = "CAUSE"
    EFFECT = "EFFECT"
    TIME = "TIME"
    PLACE = "PLACE"
    PERSON = "PERSON"
    MEMORY = "MEMORY"
    HYPOTHESIS = "HYPOTHESIS"
    CONTRADICTION = "CONTRADICTION"
    PLAN = "PLAN"
    WORD = "WORD"
    MORPHEME = "MORPHEME"
    CONCEPT = "CONCEPT"
    ANSWER = "ANSWER"


class MutationOp(str, Enum):
    CREATE = "CREATE"
    LINK = "LINK"
    UNLINK = "UNLINK"
    ACTIVATE = "ACTIVATE"
    SUPPRESS = "SUPPRESS"
    UPDATE = "UPDATE"
    MERGE = "MERGE"
    RETRACT = "RETRACT"


@dataclass
class GraphCard:
    id: str
    type: NodeType
    label: str
    latent: list[float] = field(default_factory=list)
    confidence: float = 1.0
    activation: float = 0.0
    importance: float = 0.0
    prediction_error: float = 0.0
    consolidation_strength: float = 0.0
    provenance: str = "runtime"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("GraphCard.id must be non-empty")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be within [0,1]")
        if not isinstance(self.type, NodeType):
            self.type = NodeType(self.type)


@dataclass
class TypedHyperEdge:
    id: str
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    relation: str
    confidence: float = 1.0
    provenance: str = "runtime"
    active: bool = True
    latent: list[float] = field(default_factory=list)
    consolidation_strength: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.sources or not self.targets or not self.relation:
            raise ValueError("edge id, sources, targets and relation are required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be within [0,1]")


@dataclass
class GraphUpdate:
    op: MutationOp
    target_id: str
    graph_version: int
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnswerGraph:
    answer_value: str | None
    confidence: float
    intent: str
    support_node_ids: tuple[str, ...] = ()
    support_edge_ids: tuple[str, ...] = ()
    provenance: str = "graph"

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be within [0,1]")


@dataclass
class GLLMResponse:
    text: str
    answer_graph: AnswerGraph
    workspace_trace: tuple[str, ...] = ()
    confidence: float = 0.0
    cognition_logits: tuple[float, ...] = ()
    cognition_steps: int = 0
    realizer_mode: str = "deterministic"
