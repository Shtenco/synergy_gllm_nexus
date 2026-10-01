from nexus_gllm.unified_v3.cognitive.task_cortex import *
from nexus_gllm.unified_v3.cognitive.language_cortex import SourceSpanRef
from nexus_gllm.unified_v3.contracts import TaskOpcode
import hashlib
class Fake:
    backend_id='fake'
    def propose_task(self,text):
        h=hashlib.sha256(text.encode()).hexdigest();s=SourceSpanRef(0,len(text),h)
        return TaskProposal(h,'fake',TaskOpcode.QUERY_RELATION,'r',('A','B'),.95,s)
def test_good_task_proposal_becomes_typed_program():
    r=TaskCortexPort(Fake()).parse('question');assert r.admission.accepted and r.task.operator_id=='r' and r.task.arguments==('a','b') and r.proposal_only
def test_bad_span_hash_fails_closed():
    class Bad:
        backend_id='bad'
        def propose_task(self,text):
            h=hashlib.sha256(text.encode()).hexdigest();return TaskProposal(h,'bad',TaskOpcode.QUERY_RELATION,'r',('a','b'),.95,SourceSpanRef(0,len(text),'0'*64))
    assert TaskCortexPort(Bad()).parse('x').task is None
def test_relation_query_requires_exactly_two_args_and_operator():
    class Bad:
        backend_id='bad'
        def propose_task(self,text):
            h=hashlib.sha256(text.encode()).hexdigest();s=SourceSpanRef(0,len(text),h);return TaskProposal(h,'bad',TaskOpcode.QUERY_RELATION,None,('a',),.99,s)
    r=TaskCortexPort(Bad()).parse('x');assert not r.admission.accepted and 'relation_query_shape_mismatch' in r.admission.reasons
def test_controlled_russian_query_baseline():
    r=TaskCortexPort(ControlledTaskBackend()).parse('Есть ли отношение parent от Анна к Борис?')
    assert r.task.opcode is TaskOpcode.QUERY_RELATION and r.task.operator_id=='parent' and r.task.arguments==('анна','борис')
