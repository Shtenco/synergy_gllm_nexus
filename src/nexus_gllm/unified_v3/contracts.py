from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any

@dataclass(frozen=True)
class Entity:
    entity_id: str

@dataclass(frozen=True)
class OperatorSymbol:
    operator_id: str
    arity: int

@dataclass(frozen=True)
class SemanticAtom:
    operator: OperatorSymbol
    arguments: tuple[Any,...]
    polarity: bool=True

@dataclass(frozen=True)
class SemanticObservation:
    atoms: tuple[SemanticAtom,...]=()

@dataclass(frozen=True)
class WorldFact:
    operator: OperatorSymbol
    arguments: tuple[Entity,...]
    polarity: bool=True

@dataclass(frozen=True)
class WorldHypothesis:
    world_id: str
    facts: tuple[WorldFact,...]=()

@dataclass(frozen=True)
class RuleHypothesis:
    rule_id: str
    property_name: str
    confidence: float

@dataclass(frozen=True)
class RuleProgram:
    hypotheses: tuple[RuleHypothesis,...]=()
    def has_property(self,name:str)->bool:
        return any(h.property_name==name and h.confidence>0 for h in self.hypotheses)
    def shape_fingerprint(self)->tuple[str,...]:
        return tuple(sorted(h.property_name for h in self.hypotheses if h.confidence>0))

class TaskOpcode(str,Enum):
    QUERY_RELATION='query_relation'

@dataclass(frozen=True)
class TaskProgram:
    opcode: TaskOpcode
    operator_id: str|None=None
    arguments: tuple[str,...]=()

@dataclass(frozen=True)
class DerivedFact:
    fact: WorldFact
    parents: tuple[WorldFact,...]=()
    rule_id: str|None=None
    depth: int=1

@dataclass(frozen=True)
class ExecutionResult:
    truth: bool|None=None
    derivation: DerivedFact|None=None
    answer: tuple[str,...]=()

class EpistemicState(str,Enum):
    PROVED='PROVED'; DISPROVED='DISPROVED'; UNRESOLVED='UNRESOLVED'; CONFLICTED='CONFLICTED'

@dataclass(frozen=True)
class EpistemicResult:
    state: EpistemicState
    answer: tuple[str,...]=()
    confidence: float=0.0

@dataclass(frozen=True)
class GeneralizationAudit:
    stable: bool
    invariance_rate: float
    intervention_sensitivity: float
    violations: tuple[str,...]=()
    confidence: float=0.0

@dataclass(frozen=True)
class TraceEvent:
    kind: str
    detail: str=''

@dataclass(frozen=True)
class V3Response:
    text: str
    epistemic: EpistemicResult
    execution: ExecutionResult
    generalization: GeneralizationAudit
    rule_program: RuleProgram
    task_program: TaskProgram
    trace: tuple[TraceEvent,...]=()
