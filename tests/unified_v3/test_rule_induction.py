from nexus_gllm.unified_v3.rule_induction import RuleDemonstration, RuleInducer

def chain(op,a,b,c,positive=True): return RuleDemonstration.chain(op,a,b,c,positive)

def test_nonce_operator_rename_preserves_rule_shape():
    r1=RuleInducer().induce((chain('op:zurit','a','b','c'),chain('op:zurit','d','e','f')))
    r2=RuleInducer().induce((chain('op:kema','u','v','w'),chain('op:kema','x','y','z')))
    assert r1.shape_fingerprint()==r2.shape_fingerprint()
    assert r1.has_property('transitive')

def test_negative_demo_blocks_transitivity():
    p=RuleInducer().induce((chain('op:q','a','b','c',False),))
    assert not p.has_property('transitive')
