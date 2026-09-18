from nexus_gllm.unified_v3.contracts import *
from nexus_gllm.unified_v3.counterfactual import CounterfactualEngine, world_fingerprint
def test_counterfactual_remove_does_not_mutate_actual_world():
    op=OperatorSymbol('op:q',2); f1=WorldFact(op,(Entity('a'),Entity('b'))); f2=WorldFact(op,(Entity('b'),Entity('c')))
    w=WorldHypothesis('actual',(f1,f2)); before=world_fingerprint(w)
    cf=CounterfactualEngine().apply(w,(Intervention(InterventionKind.REMOVE_FACT,fact=f2),))
    assert len(cf.facts)==1 and world_fingerprint(w)==before and len(w.facts)==2
