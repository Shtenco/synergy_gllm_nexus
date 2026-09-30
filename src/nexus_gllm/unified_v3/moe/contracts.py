from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any

class ExpertMode(str,Enum): ACTIVE='ACTIVE'; SHADOW='SHADOW'; DISABLED='DISABLED'
class ExpertProvenanceKind(str,Enum): EXACT_HISTORICAL='EXACT_HISTORICAL'; ADAPTER_RECONSTRUCTION='ADAPTER_RECONSTRUCTION'; NATIVE_V3='NATIVE_V3'
class ExpertFailureFlag(str,Enum): LOAD_FAILED='LOAD_FAILED'; HASH_MISMATCH='HASH_MISMATCH'; TIMEOUT='TIMEOUT'; MALFORMED='MALFORMED'; EXCEPTION='EXCEPTION'
class CapabilityTag(str,Enum):
    FAST_INDUCTION='FAST_INDUCTION'; LANGUAGE='LANGUAGE'; SEMANTIC_MEMORY='SEMANTIC_MEMORY'; FORMAL='FORMAL'; PROOF='PROOF'; MORPHOLOGY='MORPHOLOGY'; EVIDENCE='EVIDENCE'; CONTEXT='CONTEXT'; GRAPH='GRAPH'; PROCEDURAL='PROCEDURAL'; OPEN_SET='OPEN_SET'; HYPOTHESIS='HYPOTHESIS'

@dataclass(frozen=True)
class ExpertContext:
    semantic_observation: Any=None
    world: Any=None
    task_hypotheses: tuple[Any,...]=()
    support_demonstrations: tuple[Any,...]=()
    dialogue_state: Any=None
    metadata: dict[str,Any]|None=None
    def meta(self): return self.metadata or {}

@dataclass(frozen=True)
class ExpertProposal:
    proposal_id:str
    expert_id:str
    capability:CapabilityTag
    semantic_facts:tuple[Any,...]=()
    world_hypotheses:tuple[Any,...]=()
    rule_hypotheses:tuple[Any,...]=()
    task_hypotheses:tuple[Any,...]=()
    answer_candidates:tuple[Any,...]=()
    proof_steps:tuple[Any,...]=()
    evidence_items:tuple[Any,...]=()
    confidence:float=0.0
    uncertainty:float=1.0
    provenance:tuple[str,...]=()
    compute_cost:float=0.0
    latency_ms:float=0.0
    failure_flags:tuple[str,...]=()

@dataclass(frozen=True)
class ExpertSpec:
    expert_id:str
    version:str
    capability_tags:tuple[CapabilityTag,...]
    lineage_group:str
    artifact_path:str|None
    artifact_sha256:str|None
    adapter_class:str
    active_mode:ExpertMode=ExpertMode.ACTIVE
    max_latency_ms:int=2000
    confidence_cap:float=1.0
    provenance_kind:ExpertProvenanceKind=ExpertProvenanceKind.ADAPTER_RECONSTRUCTION

@dataclass(frozen=True)
class RoutingDecision:
    selected_experts:tuple[str,...]
    scores:tuple[tuple[str,float],...]=()
    widened:bool=False

@dataclass(frozen=True)
class FusedProposalSet:
    leading_answer:Any=None
    accepted_facts:tuple[Any,...]=()
    competing_answers:tuple[tuple[Any,float],...]=()
    conflicts:tuple[Any,...]=()
    provenance:tuple[str,...]=()
