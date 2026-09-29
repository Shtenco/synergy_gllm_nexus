from dataclasses import dataclass
from enum import Enum
class LearningTier(str,Enum): FAST="FAST";MEDIUM="MEDIUM";SLOW="SLOW"
@dataclass(frozen=True)
class PromotionEvidence:
    provenance_complete:bool;regression_delta:float;calibration_delta:float=0.0;frozen_candidate:bool=False;replay_passed:bool=False
class ContinualLearningPolicy:
    def tier_for(self,change_kind):
        if change_kind in {"raw_memory","episode"}:return LearningTier.FAST
        if change_kind in {"semantic_memory","causal_memory","self_model","router_reliability","calibration"}:return LearningTier.MEDIUM
        return LearningTier.SLOW
    def allow(self,change_kind,evidence=None):
        tier=self.tier_for(change_kind)
        if tier is not LearningTier.SLOW:return True
        if evidence is None:return False
        return bool(evidence.provenance_complete and evidence.frozen_candidate and evidence.replay_passed and evidence.regression_delta>=0 and evidence.calibration_delta<=.02)
