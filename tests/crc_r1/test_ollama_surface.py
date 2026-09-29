from nexus_gllm.unified_v3.cognitive.generative import *
from nexus_gllm.unified_v3.cognitive.generative_admission import *
from nexus_gllm.unified_v3.cognitive.generative_registry import GenerativeCortexRegistry
from nexus_gllm.unified_v3.cognitive.ollama_surface import OllamaModelRef,OllamaSurfaceBackend
from nexus_gllm.unified_v3.cognitive.generative_selector import GenerativeBackendSelector
from nexus_gllm.unified_v3.contracts import EpistemicState
class T:
    def __init__(self,text):self.text=text;self.last=None
    def post_json(self,url,payload,timeout):self.last=(url,payload,timeout);return {'response':self.text}
def spec(mid='llama3.3'):
    return GenerativeArtifactSpec(mid,GenerativeArtifactKind.CHECKPOINT,'a'*64,1_000_000,'ollama',True)
def metrics():return GenerativeEvalMetrics(.999,.999,.001,0,True)
def contract():return SurfaceContract(EpistemicState.PROVED,('42',),(),('42',))
def test_ollama_adapter_only_generates_surface_text():
    t=T('Ответ: 42.');b=OllamaSurfaceBackend(OllamaModelRef('llama3.3','a'*64),t);assert b.generate(contract())=='Ответ: 42.';assert t.last[1]['stream'] is False
def test_selector_refuses_unadmitted_backend():
    b=OllamaSurfaceBackend(OllamaModelRef('llama3.3','a'*64),T('Ответ: 42.'));c=GenerativeBackendSelector().choose((b,));r=c.realize(contract());assert r.backend_id=='deterministic_v3'
def test_selector_mounts_admitted_backend_but_guard_still_controls_output():
    reg=GenerativeCortexRegistry();assert reg.register(spec(),metrics()).admitted
    b=OllamaSurfaceBackend(OllamaModelRef('llama3.3','a'*64),T('Ответ: 999.'));c=GenerativeBackendSelector(reg).choose((b,));r=c.realize(contract());assert r.used_fallback and r.backend_id=='deterministic_v3'
