from nexus_gllm.unified_v3.cognitive.ollama_ingress import *
from nexus_gllm.unified_v3.cognitive.ollama_surface import OllamaModelRef
from nexus_gllm.unified_v3.cognitive.language_cortex import LanguageCortexPort
from nexus_gllm.unified_v3.cognitive.task_cortex import TaskCortexPort
class T:
    def __init__(self,response):self.response=response;self.last=None
    def post_json(self,url,payload,timeout):self.last=(url,payload,timeout);return {'response':self.response}
def ref():return OllamaModelRef('qwen','a'*64)
def test_neural_language_backend_offsets_are_rehashed_by_nexus():
    text='Анна любит чай';raw='{"atoms":[{"operator_id":"op:likes","arguments":["Анна","чай"],"polarity":true,"confidence":0.95,"start":0,"end":14}]}'
    b=OllamaLanguageCortexBackend(ref(),T(raw));r=LanguageCortexPort(b).parse(text)
    assert r.admission.accepted and r.observation.atoms[0].operator.operator_id=='op:likes'
def test_neural_task_backend_yields_typed_task_only():
    text='Есть ли r от a к b?';raw='{"opcode":"query_relation","operator_id":"r","arguments":["a","b"],"confidence":0.96,"start":0,"end":19}'
    b=OllamaTaskCortexBackend(ref(),T(raw));r=TaskCortexPort(b).parse(text)
    assert r.admission.accepted and r.task.operator_id=='r' and r.proposal_only
def test_task_backend_rejects_out_of_bounds_source_span():
    text='Есть ли r от a к b?';raw='{"opcode":"query_relation","operator_id":"r","arguments":["a","b"],"confidence":0.96,"start":0,"end":20}'
    r=TaskCortexPort(OllamaTaskCortexBackend(ref(),T(raw))).parse(text)
    assert not r.admission.accepted and r.task is None and r.admission.reasons[0].startswith('backend_exception:')
def test_invalid_model_json_fails_closed_in_port():
    b=OllamaLanguageCortexBackend(ref(),T('not json'));r=LanguageCortexPort(b).parse('x')
    assert not r.admission.accepted and r.observation.atoms==() and r.admission.reasons[0].startswith('backend_exception:')
def test_unknown_task_opcode_fails_closed():
    raw='{"opcode":"invent_world","operator_id":null,"arguments":[],"confidence":0.99,"start":0,"end":1}'
    r=TaskCortexPort(OllamaTaskCortexBackend(ref(),T(raw))).parse('x')
    assert not r.admission.accepted and r.task is None
