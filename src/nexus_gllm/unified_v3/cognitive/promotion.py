from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
@dataclass(frozen=True)
class ReplayMetrics:
    task_score:float
    calibration_error:float
    regression_count:int=0
@dataclass(frozen=True)
class PromotionCandidate:
    candidate_id:str
    artifact_sha256:str
    baseline:ReplayMetrics
    candidate:ReplayMetrics
    replay_passed:bool
    provenance_complete:bool
@dataclass(frozen=True)
class PromotionDecision:
    promoted:bool
    reasons:tuple[str,...]
    candidate_id:str
    artifact_sha256:str
class GuardedPromotionGate:
    def __init__(self,*,max_task_regression=0.0,max_calibration_regression=.02,max_regression_count=0):
        self.max_task_regression=float(max_task_regression);self.max_calibration_regression=float(max_calibration_regression);self.max_regression_count=int(max_regression_count)
    def decide(self,c):
        reasons=[]
        if not c.provenance_complete:reasons.append('provenance_incomplete')
        if not c.replay_passed:reasons.append('replay_failed')
        if len(c.artifact_sha256)!=64:reasons.append('invalid_sha256')
        if c.candidate.task_score < c.baseline.task_score-self.max_task_regression:reasons.append('task_regression')
        if c.candidate.calibration_error > c.baseline.calibration_error+self.max_calibration_regression:reasons.append('calibration_regression')
        if c.candidate.regression_count>self.max_regression_count:reasons.append('anti_forgetting_regressions')
        return PromotionDecision(not reasons,tuple(reasons),c.candidate_id,c.artifact_sha256)
    @staticmethod
    def manifest(candidate,decision):
        return {'candidate_id':candidate.candidate_id,'artifact_sha256':candidate.artifact_sha256,'baseline':candidate.baseline.__dict__,'candidate':candidate.candidate.__dict__,'replay_passed':candidate.replay_passed,'provenance_complete':candidate.provenance_complete,'promoted':decision.promoted,'reasons':decision.reasons}
