from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any

@dataclass(frozen=True)
class Entity: entity_id: str
@dataclass(frozen=True)
class OperatorSymbol: operator_id: str; arity: int
@dataclass(frozen=True)
class SemanticAtom: operator: OperatorSymbol; arguments: tuple[Any,...]; polarity: bool=True
@dataclass(frozen=True)
class SemanticObservation: atoms: tuple[SemanticAtom,...]=()
@dataclass(frozen=True)
class WorldFact: operator: OperatorSymbol; arguments: tuple[Entity,...]; polarity: bool=True
@dataclass(frozen=True)
class WorldHypothesis: world_id: str; facts: tuple[WorldFact,...]=(); parent_world_id: str|None=None
@dataclass(frozen=True)
class RuleHypothesis: rule_id: str; property_name: str; confidence: float
@dataclass(frozen=True)
class RuleProgram:
    hypotheses: tuple[RuleHypothesis,...]=()
    clauses: tuple[Any,...]=()
    def has_property(self,name:str)->bool:
        return any(h.property_name==name and h.confidence>0 for h in self.hypotheses) or any(getattr(c,'family',None) is not None and getattr(getattr(c,'family',None),'value',None).lower()==name.lower() for c in self.clauses)
    def shape_fingerprint(self)->tuple[str,...]:
        a=[h.property_name for h in self.hypotheses if h.confidence>0]
        a += [getattr(c.family,'value',str(c.family)) for c in self.clauses]
        return tuple(sorted(a))
class TaskOpcode(str,Enum):
    QUERY_RELATION='query_relation'; SELECT_ENTITY='select_entity'; EXTRACT_SET='extract_set'; ORDER_TUPLE='order_tuple'; EPISTEMIC_STATUS='epistemic_status'; FIND_PROOF='find_proof'; FIND_MINIMAL_PROOF='find_minimal_proof'; COMPARE_WORLDS='compare_worlds'; COUNTERFACTUAL_QUERY='counterfactual_query'; CURRENT_STATE='current_state'; HISTORICAL_STATE='historical_state'
@dataclass(frozen=True)
class TaskProgram: opcode: TaskOpcode; operator_id: str|None=None; arguments: tuple[str,...]=()
@dataclass(frozen=True)
class DerivedFact:
    fact: WorldFact; parents: tuple[WorldFact,...]=(); rule_id: str|None=None; depth: int=1; hypothesis_id: str|None=None; world_id: str|None=None
@dataclass(frozen=True)
class ExecutionResult: truth: bool|None=None; derivation: DerivedFact|None=None; answer: tuple[str,...]=()
class EpistemicState(str,Enum): PROVED='PROVED'; DISPROVED='DISPROVED'; UNRESOLVED='UNRESOLVED'; CONFLICTED='CONFLICTED'
@dataclass(frozen=True)
class EpistemicResult:
    state: EpistemicState; answer: tuple[str,...]=(); confidence: float=0.0; support_mass: float=0.0; contradiction_mass: float=0.0; unresolved_mass: float=0.0
@dataclass(frozen=True)
class GeneralizationAudit: stable: bool; invariance_rate: float; intervention_sensitivity: float; violations: tuple[str,...]=(); confidence: float=0.0
@dataclass(frozen=True)
class TraceEvent: kind: str; detail: str=''
@dataclass(frozen=True)
class V3Response:
    text: str; epistemic: EpistemicResult; execution: ExecutionResult; generalization: GeneralizationAudit; rule_program: RuleProgram; task_program: TaskProgram; trace: tuple[TraceEvent,...]=()

class HypothesisStatus(str,Enum): ACTIVE='ACTIVE'; PRUNED='PRUNED'; FALSIFIED='FALSIFIED'; DOMINATED='DOMINATED'; FORKED='FORKED'
class FactLifecycle(str,Enum): ACTIVE='ACTIVE'; SUPERSEDED='SUPERSEDED'; RETRACTED='RETRACTED'; TEMPORARY='TEMPORARY'; CONDITIONAL='CONDITIONAL'
class PredictionOutcome(str,Enum): PENDING='PENDING'; CONFIRMED='CONFIRMED'; REFUTED='REFUTED'; UNOBSERVED='UNOBSERVED'
class ConflictResolution(str,Enum): UNRESOLVED='UNRESOLVED'; CONFLICTED='CONFLICTED'; SUPERSEDED='SUPERSEDED'; RESOLVED_POSITIVE='RESOLVED_POSITIVE'; RESOLVED_NEGATIVE='RESOLVED_NEGATIVE'
class InterventionKind(str,Enum): ADD_FACT='ADD_FACT'; REMOVE_FACT='REMOVE_FACT'; FLIP_POLARITY='FLIP_POLARITY'; SET_STATE='SET_STATE'; BLOCK_RULE='BLOCK_RULE'; ENABLE_RULE='ENABLE_RULE'

@dataclass(frozen=True)
class HypothesisState:
    hypothesis_id: str; world: WorldHypothesis; rules: RuleProgram; score: float=0.0; complexity_cost: float=0.0; contradiction_cost: float=0.0; prediction_score: float=0.0; evidence_mass: float=0.0; lineage: tuple[str,...]=(); status: HypothesisStatus=HypothesisStatus.ACTIVE; rule_family: str=''
@dataclass(frozen=True)
class HypothesisBeam: active: tuple[HypothesisState,...]=(); eliminated: tuple[HypothesisState,...]=()
@dataclass(frozen=True)
class Prediction:
    prediction_id: str; hypothesis_id: str; atom: tuple[str,...]; expected_polarity: bool; outcome: PredictionOutcome=PredictionOutcome.PENDING; score_delta: float=0.0
@dataclass(frozen=True)
class FactVersion:
    relation: str; subject: str; value: str; valid_from: int; valid_until: int|None=None; lifecycle: FactLifecycle=FactLifecycle.ACTIVE; supersedes: int|None=None
@dataclass(frozen=True)
class ConflictSet:
    positive_support: tuple[str,...]=(); negative_support: tuple[str,...]=(); resolution: ConflictResolution=ConflictResolution.UNRESOLVED
@dataclass(frozen=True)
class Intervention:
    kind: InterventionKind; fact: WorldFact|None=None; payload: tuple[str,...]=()
@dataclass(frozen=True)
class CounterfactualComparison:
    changed: bool; actual_truth: bool|None; counterfactual_truth: bool|None; changed_support: tuple[str,...]=()
