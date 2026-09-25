from nexus_gllm.r13x import Proposal, R13XGovernor, R13XRouter, Verifier, Blackboard, R13XEngine

def test_exact_beats_neural_confidence():
    p=R13XGovernor().resolve([
        Proposal("n","wrong",.999,.01,verification="NEURAL_PROPOSAL"),
        Proposal("x","right",.2,.5,verification="EXACT_VERIFIED"),
    ])
    assert p and p.value=="right"

def test_ood_abstains():
    assert R13XGovernor().resolve([Proposal("n","guess",.9,.99,verification="NEURAL_PROPOSAL")]) is None

def test_same_authority_conflict_abstains():
    assert R13XGovernor().resolve([
        Proposal("a",True,.9,.1,verification="DIRECT_EVIDENCE"),
        Proposal("b",False,.9,.1,verification="DIRECT_EVIDENCE"),
    ]) is None

def test_blackboard_keeps_competing_hypotheses():
    b=Blackboard()
    b.add(Proposal("a",1,.7,.2,verification="NEURAL_PROPOSAL"))
    b.add(Proposal("b",2,.6,.2,verification="NEURAL_PROPOSAL"))
    assert len(b.proposals)==2

def test_router_is_deterministic():
    r=R13XRouter()
    assert r.route({"graph":1.0},["semantic","exact","evidence","causal"]) == r.route({"graph":1.0},["semantic","exact","evidence","causal"])

def test_verifier_exact_arithmetic():
    v=Verifier()
    p=Proposal("calc",0,.8,.0,verification="NEURAL_PROPOSAL",verification_op="CALCULATE",metadata={"expression":"2+2"})
    q=v.verify(p)
    assert q.verification=="EXACT_VERIFIED"
