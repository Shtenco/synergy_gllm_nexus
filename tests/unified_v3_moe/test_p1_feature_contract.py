from nexus_gllm.unified_v3.moe.capability_router import RouterFeatures
from nexus_gllm.unified_v3.moe.learned_router import LoadableCapabilityRouter
def test_p1_tensorization_preserves_explicit_continuous_signals():
    f=RouterFeatures(support_count=2,language='en',evidence_conflict=False,context_depth=1,graph_signal=.3,proof_signal=.4,novelty=.5,cost_signal=.6,ru_signal=.73,evidence_signal=.61)
    x=LoadableCapabilityRouter.feature_vector(f);assert x==(0.5,.73,.61,.25,.3,.5,.4,.6)
def test_p1_tensorization_falls_back_to_semantic_booleans():
    f=RouterFeatures(support_count=4,language='ru',evidence_conflict=True,context_depth=0)
    x=LoadableCapabilityRouter.feature_vector(f);assert x[0]==1 and x[1]==1 and x[2]==1
