from __future__ import annotations
from .promotion import ReplayMetrics,PromotionCandidate
from .replay_bank import ReplayReport

def promotion_candidate_from_replay(candidate_id,artifact_sha256,report:ReplayReport,*,provenance_complete=True,replay_passed=True):
    baseline=ReplayMetrics(report.baseline_score,0.0,0)
    candidate=ReplayMetrics(report.candidate_score,max(0.0,report.calibration_delta),report.regression_count)
    return PromotionCandidate(candidate_id,artifact_sha256,baseline,candidate,replay_passed,provenance_complete)
