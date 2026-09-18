from nexus_gllm.unified_v3.contracts import *
from nexus_gllm.unified_v3.epistemic import EpistemicController
from nexus_gllm.unified_v3.generalization import GeneralizationGovernor
def test_fragmented_mass_remains_unresolved_but_aligned_mass_proves():
    c=EpistemicController(0.7)
    assert c.resolve_weighted(((ExecutionResult(True),0.51),(ExecutionResult(False),0.49))).state is EpistemicState.UNRESOLVED
    assert c.resolve_weighted(((ExecutionResult(True),0.8),(ExecutionResult(True),0.2))).state is EpistemicState.PROVED
def test_hypothesis_shape_stability():
    assert GeneralizationGovernor().hypothesis_stability((('TRANSITIVE',0),('SYMMETRIC',1)),(('TRANSITIVE',0),('SYMMETRIC',1)))==1.0
