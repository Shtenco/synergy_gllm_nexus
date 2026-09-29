from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re

class GenerativeArtifactKind(str,Enum):
    CHECKPOINT='CHECKPOINT'
    GGUF='GGUF'
    SAFETENSORS='SAFETENSORS'
    SOURCE='SOURCE'
    EVIDENCE='EVIDENCE'
    UNKNOWN='UNKNOWN'

@dataclass(frozen=True)
class GenerativeArtifactSpec:
    model_id:str
    artifact_kind:GenerativeArtifactKind
    sha256:str
    size_bytes:int
    architecture:str=''
    surface_only:bool=True

@dataclass(frozen=True)
class GenerativeEvalMetrics:
    semantic_fidelity:float
    guard_pass_rate:float
    hallucination_rate:float
    regression_count:int
    frozen_eval:bool

@dataclass(frozen=True)
class GenerativeAdmissionDecision:
    admitted:bool
    reasons:tuple[str,...]

class GenerativeCortexAdmissionGate:
    """Admit only a frozen runnable model payload with strong surface fidelity."""
    RUNNABLE={GenerativeArtifactKind.CHECKPOINT,GenerativeArtifactKind.GGUF,GenerativeArtifactKind.SAFETENSORS}
    def __init__(self,*,min_fidelity=.99,min_guard_pass=.99,max_hallucination=.01,max_regressions=0):
        self.min_fidelity=float(min_fidelity);self.min_guard_pass=float(min_guard_pass);self.max_hallucination=float(max_hallucination);self.max_regressions=int(max_regressions)
    def decide(self,spec:GenerativeArtifactSpec,metrics:GenerativeEvalMetrics)->GenerativeAdmissionDecision:
        reasons=[]
        if spec.artifact_kind not in self.RUNNABLE:reasons.append('not_runnable_model_payload')
        if spec.size_bytes<=0:reasons.append('empty_payload')
        if not re.fullmatch(r'[0-9a-fA-F]{64}',spec.sha256):reasons.append('invalid_sha256')
        if not spec.surface_only:reasons.append('authority_boundary_violation')
        if not metrics.frozen_eval:reasons.append('evaluation_not_frozen')
        if metrics.semantic_fidelity<self.min_fidelity:reasons.append('semantic_fidelity_below_gate')
        if metrics.guard_pass_rate<self.min_guard_pass:reasons.append('guard_pass_below_gate')
        if metrics.hallucination_rate>self.max_hallucination:reasons.append('hallucination_above_gate')
        if metrics.regression_count>self.max_regressions:reasons.append('surface_regressions')
        return GenerativeAdmissionDecision(not reasons,tuple(reasons))
