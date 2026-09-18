from nexus_gllm.unified_v3.runtime import UnifiedNexusV3P0
from nexus_gllm.unified_v3.rule_algebra import RuleFamily
def test_hypothesis_episode_reranks_and_counterfactuals():
    out=UnifiedNexusV3P0().respond_hypothesis_episode(operator_id='op:q',edges=(('a','b'),('b','c')),query=('a','c'),evidence=((RuleFamily.TRANSITIVE,True),),counterfactual_remove=(('b','c'),))
    assert out['beam'].active[0].rule_family=='TRANSITIVE'
    assert out['actual'].truth is True
    assert out['counterfactual'].truth is None
