from nexus_gllm.unified_v3.cognitive.dialogue_context import *
def test_latest_referent_resolves_within_boundary():
    c=DialogueContextR1('s');c.mention('она','alice',.8);c.mention('она','olga',.9);assert c.resolve('она').entity_id=='olga'
def test_hard_boundary_clears_referents_and_pending_slots_not_history():
    c=DialogueContextR1('s');c.mention('он','a');c.open_slot('f','city');c.set_value('profile.name','Alice');c.hard_boundary('new_topic')
    assert c.resolve('он') is None and c.state.pending_slots==() and c.current('profile.name').value=='Alice' and c.state.boundary_id==1
def test_pending_slot_fill_creates_context_value():
    c=DialogueContextR1('s');c.open_slot('trip','city');v=c.fill_slot('trip','city','Костанай');assert v.value=='Костанай' and c.unresolved_required_slots()==()
def test_verified_value_blocks_lower_authority_assertion():
    c=DialogueContextR1('s');c.set_value('tax.rate','12',status=ContextValueStatus.VERIFIED,provenance_id='proof');v=c.set_value('tax.rate','99',status=ContextValueStatus.ASSERTED)
    assert v.value=='12' and c.current('tax.rate').value=='12' and 'assertion_blocked_by_verified:tax.rate' in c.state.trace
def test_new_verified_value_can_supersede_old_verified_value_with_history():
    c=DialogueContextR1('s');a=c.set_value('x','old',status=ContextValueStatus.VERIFIED);b=c.set_value('x','new',status=ContextValueStatus.VERIFIED)
    assert c.current('x')==b and any(v.value=='old' and v.status is ContextValueStatus.SUPERSEDED for v in c.state.values)
