from nexus_gllm.unified_v3.contracts import *
from nexus_gllm.unified_v3.hypothesis_search import HypothesisSearch, EvidenceSignal
from nexus_gllm.unified_v3.rule_algebra import RuleClause
def test_underdetermined_beam_retains_competing_theories_and_reranks():
    w=WorldHypothesis('w',()); hs=HypothesisSearch(8)
    beam=hs.seed((w,),(RuleClause.transitive('op:q'),RuleClause.symmetric('op:q')))
    assert len(beam.active)>=2
    reranked=hs.rescore(beam,(EvidenceSignal(RuleFamilyName='TRANSITIVE',confirmed=True),))
    assert reranked.active[0].rule_family=='TRANSITIVE'
def test_structural_rank_is_operator_name_invariant():
    hs=HypothesisSearch(); w=WorldHypothesis('w',())
    a=hs.seed((w,),(RuleClause.transitive('op:a'),RuleClause.symmetric('op:a')))
    b=hs.seed((w,),(RuleClause.transitive('op:z'),RuleClause.symmetric('op:z')))
    assert [x.rule_family for x in a.active]==[x.rule_family for x in b.active]
