from nexus_gllm.unified_v3.cognitive.causal_model import *
from benchmarks.causal_m15.run import generate,evaluate
def test_observational_correlation_never_identifies_causality_alone():
    g=CausalGraph();g.add(CausalEvidence('o','x','y',CausalEvidenceKind.OBSERVATIONAL,1,.99))
    e=g.edge('x','y');assert not e.identified and e.observational_mass>0
def test_intervention_plus_counterfactual_can_identify_edge():
    g=CausalGraph();g.add(CausalEvidence('i','x','y',CausalEvidenceKind.INTERVENTIONAL,.9,.95));g.add(CausalEvidence('c','x','y',CausalEvidenceKind.COUNTERFACTUAL,.8,.9))
    assert g.edge('x','y').identified
def test_trusted_negative_intervention_blocks_causal_claim():
    g=CausalGraph();g.add(CausalEvidence('o','x','y',CausalEvidenceKind.OBSERVATIONAL,1,1));g.add(CausalEvidence('i','x','y',CausalEvidenceKind.INTERVENTIONAL,-1,1))
    assert not g.edge('x','y').identified
def test_descendants_follow_identified_edges_only():
    g=CausalGraph()
    for a,b in [('a','b'),('b','c')]:
        g.add(CausalEvidence(a+b,a,b,CausalEvidenceKind.INTERVENTIONAL,1,1));g.add(CausalEvidence('cf'+a+b,a,b,CausalEvidenceKind.COUNTERFACTUAL,1,1))
    assert g.descendants('a')==('b','c') and g.would_cycle('c','a')
def test_interventional_benchmark_beats_correlation_only():
    cases=generate(n=40);full=evaluate(cases,True);obs=evaluate(cases,False)
    assert full['accuracy']>obs['accuracy'] and full['false_causal_rate']==0
