from nexus_gllm.unified_v3.moe.contracts import *
from nexus_gllm.unified_v3.moe.capability_router import RouterFeatures,HeuristicCapabilityRouter
from nexus_gllm.unified_v3.moe.novelty_gate import NoveltyGate,NoveltySignals,NoveltyState
from nexus_gllm.unified_v3.moe.proposal_fusion import ProposalFusion
from nexus_gllm.unified_v3.moe.registry import ExpertRegistry

def registry():
    reg=ExpertRegistry()
    specs=[
      ExpertSpec('r7l','1',(CapabilityTag.FAST_INDUCTION,), 'r7',None,None,'x'),
      ExpertSpec('r72','1',(CapabilityTag.LANGUAGE,), 'r7',None,None,'x'),
      ExpertSpec('r718','1',(CapabilityTag.EVIDENCE,), 'r718',None,None,'x'),
      ExpertSpec('v3','1',(CapabilityTag.HYPOTHESIS,), 'v3',None,None,'x'),
      ExpertSpec('graph','1',(CapabilityTag.GRAPH,), 'omega',None,None,'x')]
    for s in specs: reg.register(s)
    return reg

def test_router_selects_fast_induction_for_support():
    d=HeuristicCapabilityRouter().route(RouterFeatures(support_count=3,language='ru'),registry(),2,4)
    assert 'r7l' in d.selected_experts and 'r72' in d.selected_experts

def test_novelty_widens_to_r7l_and_v3():
    d=NoveltyGate().classify(NoveltySignals(.3,.9,.9,.95,.8,True))
    assert d.state is NoveltyState.NOVEL
    assert {'r7l','v3'}.issubset(set(d.required_experts))

def test_fusion_not_majority_vote_for_correlated_lineage():
    reg=ExpertRegistry()
    for s in [ExpertSpec('a','1',(CapabilityTag.PROOF,), 'same',None,None,'x'),ExpertSpec('b','1',(CapabilityTag.PROOF,), 'same',None,None,'x'),ExpertSpec('c','1',(CapabilityTag.EVIDENCE,), 'ind',None,None,'x')]: reg.register(s)
    ps=(ExpertProposal('1','a',CapabilityTag.PROOF,answer_candidates=('X',),confidence=.65),ExpertProposal('2','b',CapabilityTag.PROOF,answer_candidates=('X',),confidence=.65),ExpertProposal('3','c',CapabilityTag.EVIDENCE,answer_candidates=('Y',),confidence=.95,evidence_items=('independent',)))
    assert ProposalFusion().fuse(ps,reg).leading_answer=='Y'
