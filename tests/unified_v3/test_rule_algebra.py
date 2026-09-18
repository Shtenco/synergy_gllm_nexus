from nexus_gllm.unified_v3.rule_algebra import RuleFamily, RuleClause, rule_shape_fingerprint
from nexus_gllm.unified_v3.rule_induction import RuleInducer, RuleDemonstration
def test_candidate_rule_families_and_rename_invariance():
    assert {RuleFamily.SYMMETRIC,RuleFamily.INVERSE,RuleFamily.TRANSITIVE,RuleFamily.COMPOSITION,RuleFamily.CONDITIONAL,RuleFamily.BLOCKED}
    a=RuleClause.transitive('op:a'); b=RuleClause.transitive('op:renamed')
    assert rule_shape_fingerprint(a)==rule_shape_fingerprint(b)
    assert len(RuleInducer().candidates((RuleDemonstration.chain('op:q','a','b','c',True),)))>=2
