from nexus_gllm.r13x import Proposal
from nexus_gllm.r13x_unified_v3 import R13XUnifiedV3
from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, WorldFact, WorldHypothesis, Intervention, InterventionKind

def world():
    op=OperatorSymbol("related",2)
    return WorldHypothesis("w0",(WorldFact(op,(Entity("a"),Entity("b"))),))

def test_integration_exact_overrides_neural():
    r=R13XUnifiedV3().answer("q",(
        Proposal("neural","wrong",.999,.01,verification="NEURAL_PROPOSAL"),
        Proposal("exact","right",.1,.4,verification="EXACT_VERIFIED"),
    ),world=world())
    assert r.answer and r.answer.value=="right"

def test_counterfactual_is_recorded():
    w=world(); f=w.facts[0]
    r=R13XUnifiedV3().answer("q",(Proposal("n",True,.7,.1,verification="NEURAL_PROPOSAL"),),
        world=w,interventions=(Intervention(InterventionKind.REMOVE_FACT,f),))
    assert r.counterfactual_changed is True
    assert r.replay_hash

def test_same_authority_conflict_abstains():
    r=R13XUnifiedV3().answer("q",(
        Proposal("a",True,.9,.1,verification="DIRECT_EVIDENCE"),
        Proposal("b",False,.9,.1,verification="DIRECT_EVIDENCE"),
    ))
    assert r.answer is None
