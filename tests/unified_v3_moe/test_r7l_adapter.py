from nexus_gllm.unified_v3.moe.contracts import ExpertContext
from nexus_gllm.unified_v3.moe.experts.r7l_fast_induction import R7LFastInductionExpert,SupportMapping

def test_r7l_infers_heldout_state_from_three_supports():
    support=(SupportMapping(0,2,1),SupportMapping(1,0,3),SupportMapping(2,3,2))
    ctx=ExpertContext(support_demonstrations=support,metadata={'query_state':3,'intent':'execute'})
    p=R7LFastInductionExpert().propose(ctx)
    assert p.answer_candidates==(1,)
    assert p.confidence>0.9

def test_r7l_no_support_abstains():
    p=R7LFastInductionExpert().propose(ExpertContext(metadata={'query_state':1,'intent':'execute'}))
    assert p.answer_candidates==()
    assert p.uncertainty==1.0
