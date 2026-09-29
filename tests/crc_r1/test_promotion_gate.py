from nexus_gllm.unified_v3.cognitive.promotion import ReplayMetrics,PromotionCandidate,GuardedPromotionGate
from nexus_gllm.unified_v3.cognitive.continual import ContinualLearningPolicy
SHA='a'*64
def c(task=1.0,cal=.05,reg=0,replay=True,prov=True):
    return PromotionCandidate('cand',SHA,ReplayMetrics(1.0,.05,0),ReplayMetrics(task,cal,reg),replay,prov)
def test_clean_candidate_promotes():
    d=GuardedPromotionGate().decide(c());assert d.promoted and not d.reasons
def test_any_forgetting_blocks_promotion():
    d=GuardedPromotionGate().decide(c(reg=1));assert not d.promoted and 'anti_forgetting_regressions' in d.reasons
def test_calibration_regression_blocks_even_if_task_improves():
    d=GuardedPromotionGate().decide(c(task=1.1,cal=.09));assert not d.promoted and 'calibration_regression' in d.reasons
def test_slow_policy_uses_promotion_gate():
    p=ContinualLearningPolicy();assert p.allow_candidate('core_weights',c());assert not p.allow_candidate('router_weights',c(replay=False))
