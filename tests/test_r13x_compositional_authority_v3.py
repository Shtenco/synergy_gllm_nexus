from nexus_gllm.r13x_compositional_authority_v3 import CompositionalAuthorityGovernorV3

class FakeExact:
    def __init__(self,sem=None,proof=None):
        self.sem=sem
        self.pr=proof
    def semantic_answer(self,q,min_similarity=.55):
        return self.sem
    def proof(self,q):
        return self.pr

def verified(rule,conclusion):
    return {"status":"VERIFIED","conclusion":conclusion,"ir":{"compiler_rule":rule,"source":"q"},"proof":{},"verification":{}}

def test_known_wrong_semantic_loses_to_full_proof():
    g=CompositionalAuthorityGovernorV3(FakeExact(
        {"answer":"2","atom_id":"P04","governor_correct":False,"similarity":1.0},
        verified("py_floordiv",3)
    ))
    d=g.decide("В Python чему равно 7 // 2?")
    assert d.answer==3
    assert d.authority=="R710_VERIFIED_FULL_SCOPE"

def test_partial_proof_is_composed_safely():
    g=CompositionalAuthorityGovernorV3(FakeExact(
        {"answer":"5","atom_id":"P01","governor_correct":False,"similarity":1.0},
        verified("py_range",[2,4,6,8])
    ))
    d=g.decide("В Python чему равно len(list(range(2, 10, 2)))?")
    assert d.answer==4
    assert d.authority=="COMPOSED_VERIFIED_EXECUTION"
    assert d.proof_scope=="PARTIAL_SCOPE"

def test_unsupported_outer_composition_fails_closed():
    g=CompositionalAuthorityGovernorV3(FakeExact(
        {"answer":"5","atom_id":"P01","governor_correct":False,"similarity":.9},
        verified("py_range",[2,4,6,8])
    ))
    d=g.decide("В Python чему равно tuple(range(2, 10, 2))?")
    assert d.status=="ABSTAIN"
    assert d.authority=="PARTIAL_PROOF_FAIL_CLOSED"

def test_correct_frozen_semantic_is_advisory_fallback():
    g=CompositionalAuthorityGovernorV3(FakeExact(
        {"answer":"O(1)","atom_id":"P02","governor_correct":True,"similarity":1.0},
        None
    ))
    d=g.decide("hash table")
    assert d.answer=="O(1)"
    assert d.authority=="R76_ACCEPTED_FROZEN_SEMANTIC"

def test_known_wrong_semantic_without_proof_is_quarantined():
    g=CompositionalAuthorityGovernorV3(FakeExact(
        {"answer":"wrong","atom_id":"X","governor_correct":False,"similarity":1.0},
        None
    ))
    d=g.decide("q")
    assert d.status=="ABSTAIN"
    assert d.authority=="QUARANTINED_SEMANTIC_NO_PROOF"
