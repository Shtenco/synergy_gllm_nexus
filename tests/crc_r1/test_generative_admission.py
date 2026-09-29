from nexus_gllm.unified_v3.cognitive.generative_admission import *
from nexus_gllm.unified_v3.cognitive.generative_registry import GenerativeCortexRegistry
SHA='a'*64
def good_spec(kind=GenerativeArtifactKind.SAFETENSORS,size=1000000):
    return GenerativeArtifactSpec('m',kind,SHA,size,'qwen',True)
def good_metrics():
    return GenerativeEvalMetrics(.995,.999,.001,0,True)
def test_source_archive_cannot_be_admitted_as_model():
    d=GenerativeCortexAdmissionGate().decide(good_spec(GenerativeArtifactKind.SOURCE,123599),good_metrics());assert not d.admitted and 'not_runnable_model_payload' in d.reasons
def test_evidence_archive_cannot_be_admitted_as_model():
    d=GenerativeCortexAdmissionGate().decide(good_spec(GenerativeArtifactKind.EVIDENCE,2799),good_metrics());assert not d.admitted
def test_good_frozen_surface_checkpoint_can_be_admitted():
    assert GenerativeCortexAdmissionGate().decide(good_spec(),good_metrics()).admitted
def test_fluent_but_unfaithful_model_is_rejected():
    m=GenerativeEvalMetrics(.90,.999,.0,0,True);d=GenerativeCortexAdmissionGate().decide(good_spec(),m);assert not d.admitted and 'semantic_fidelity_below_gate' in d.reasons
def test_registry_only_activates_admitted_models():
    r=GenerativeCortexRegistry();r.register(good_spec(),good_metrics());assert len(r.active())==1
