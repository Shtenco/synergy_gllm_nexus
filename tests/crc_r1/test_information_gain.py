from nexus_gllm.unified_v3.cognitive.information_gain import *
from benchmarks.info_gain_m16.run import suite,run
def test_entropy_of_balanced_binary_prior_is_one_bit():
    assert abs(entropy((HypothesisMass('a',.5),HypothesisMass('b',.5)))-1)<1e-12
def test_diagnostic_query_has_large_information_gain():
    prior,qs=suite();s=ActiveInformationSelector().score(prior,qs[0]);assert s.information_gain>.6
def test_risky_perfect_query_can_lose_to_safer_diagnostic():
    assert run()['selected']=='diagnostic'
def test_uninformative_query_has_zero_gain():
    p=(HypothesisMass('a',.5),HypothesisMass('b',.5));q=InformationQuery('x',(QueryOutcome('same',1,p),))
    assert ActiveInformationSelector().score(p,q).information_gain==0
