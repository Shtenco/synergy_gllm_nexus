from nexus_gllm.unified_v3.cognitive.belief_state import *
def test_conflicting_verified_beliefs_remain_conflicted():
    l=BeliefLedger();l.add('weather','rain',status=BeliefStatus.VERIFIED,confidence=.9,provenance_ids=('a',));l.add('weather','sun',status=BeliefStatus.VERIFIED,confidence=.9,provenance_ids=('b',))
    r=l.resolve('weather');assert r.status is BeliefStatus.CONFLICTED and r.preferred is None
def test_verified_beats_unverified_without_deleting_history():
    l=BeliefLedger();l.add('k','guess',status=BeliefStatus.PROPOSED,confidence=.99);v=l.add('k','truth',status=BeliefStatus.VERIFIED,confidence=.8)
    r=l.resolve('k');assert r.status is BeliefStatus.VERIFIED and r.preferred==v and len(r.active)==2
def test_asserted_context_is_not_verified():
    l=BeliefLedger();a=l.add('name','Alice',status=BeliefStatus.ASSERTED,confidence=.9);r=l.resolve('name');assert r.status is BeliefStatus.ASSERTED and r.preferred==a
def test_supersede_preserves_revision_chain():
    l=BeliefLedger();a=l.add('city','old',status=BeliefStatus.ASSERTED);b=l.supersede(a.belief_id,'new',status=BeliefStatus.ASSERTED)
    assert l.get(a.belief_id).status is BeliefStatus.SUPERSEDED and b.parent_ids==(a.belief_id,) and b.revision==2
