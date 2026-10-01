from nexus_gllm.unified_v3.cognitive.meta_controller import MetaController
from nexus_gllm.unified_v3.cognitive.self_model import NexusSelfModel
from nexus_gllm.unified_v3.cognitive.state import ComputeBudget

def budget():return ComputeBudget(1,3,4,4,16)

def train(sm,cap,successes,failures):
    for _ in range(successes):sm.observe(cap,success=True)
    for _ in range(failures):sm.observe(cap,success=False)

def test_weak_capability_increases_compute_and_verification():
    sm=NexusSelfModel();train(sm,'counterfactual',1,9)
    m=MetaController();base=m.decide(novelty=.2,uncertainty=.3,budget=budget(),self_model=sm)
    weak=m.decide(novelty=.2,uncertainty=.3,budget=budget(),self_model=sm,capability_hints=('counterfactual',))
    assert weak.branch_depth>=base.branch_depth
    assert weak.expert_top_k>=base.expert_top_k
    assert weak.verification_level>base.verification_level
    assert 'counterfactual' in weak.weak_capabilities

def test_strong_capability_does_not_inflate_compute():
    sm=NexusSelfModel();train(sm,'formal',20,0)
    m=MetaController();a=m.decide(novelty=.2,uncertainty=.2,budget=budget(),self_model=sm)
    b=m.decide(novelty=.2,uncertainty=.2,budget=budget(),self_model=sm,capability_hints=('formal',))
    assert b.branch_depth==a.branch_depth and b.expert_top_k==a.expert_top_k

def test_extreme_known_weakness_plus_uncertainty_can_abstain():
    sm=NexusSelfModel();train(sm,'causal',0,30)
    d=MetaController().decide(novelty=.4,uncertainty=.8,budget=budget(),self_model=sm,capability_hints=('causal',))
    assert d.abstain and d.verification_level==3
