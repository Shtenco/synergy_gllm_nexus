import json
import pytest

from nexus_gllm.unified_v3.cognitive.generalized_ingress import GeneralizedIngressR1, GeneralizedIngressRequest
from nexus_gllm.unified_v3.cognitive.generalized_ingress_ollama import OllamaGeneralizedIngressBackend
from nexus_gllm.unified_v3.cognitive.ollama_surface import OllamaModelRef
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind


class Transport:
    def __init__(self, response=None, exc=None):
        self.response=response
        self.exc=exc
        self.calls=[]
    def post_json(self,url,payload,timeout):
        self.calls.append((url,payload,timeout))
        if self.exc:
            raise self.exc
        return {'response': json.dumps(self.response)}


class MalformedJSONTransport(Transport):
    def post_json(self,url,payload,timeout):
        self.calls.append((url,payload,timeout))
        return {'response':'{'}


def make_request():
    return GeneralizedIngressRequest.from_texts('parent alice bob',history=('alice parent bob',))


def make_response(req):
    return {
      'semantic_atoms':[{'operator_id':'parent','arguments':['alice','bob'],'polarity':True,'confidence':.99,'spans':[{'source_id':'history:0','start':0,'end':16}]}],
      'task':{'opcode':'query_relation','operator_id':'parent','arguments':['alice','bob'],'confidence':.99,'spans':[{'source_id':'prompt:0','start':0,'end':16}]},
      'program':{'confidence':.99,'spans':[{'source_id':'prompt:0','start':0,'end':16}],'node':{'kind':'ATOM','symbol':'rule:transitive:parent','params':[],'children':[]}}
    }


def ref(digest='a'*64):
    return OllamaModelRef('m32-model',digest)


def test_backend_exists():
    assert OllamaGeneralizedIngressBackend is not None


def test_invalid_model_digest_is_rejected_before_transport():
    transport=Transport({})
    with pytest.raises(ValueError):
        OllamaGeneralizedIngressBackend(ref('g'*64),transport)
    assert transport.calls==[]


def test_single_call_returns_semantic_task_and_program_proposals():
    req=make_request(); transport=Transport(make_response(req))
    proposal=OllamaGeneralizedIngressBackend(ref(),transport).propose(req)
    assert len(transport.calls)==1
    assert proposal.semantic_atoms[0].supporting_spans[0].source_id=='history:0'
    assert proposal.task.supporting_spans[0].source_id=='prompt:0'
    assert proposal.program.node.kind is ProgramKind.ATOM
    assert transport.calls[0][1]['format']=='json'
    assert transport.calls[0][1]['options']['temperature']==0


def test_malformed_json_fails_closed_without_partial_output():
    result=GeneralizedIngressR1(OllamaGeneralizedIngressBackend(ref(),MalformedJSONTransport())).parse(make_request())
    assert not result.admission.accepted
    assert result.semantic_atoms==() and result.task is None and result.program is None


def test_unknown_source_id_is_rejected_by_deterministic_gate():
    req=make_request(); data=make_response(req)
    data['semantic_atoms'][0]['spans'][0]['source_id']='missing:0'
    result=GeneralizedIngressR1(OllamaGeneralizedIngressBackend(ref(),Transport(data))).parse(req)
    assert not result.admission.accepted
    assert any('unknown_source_id' in reason for reason in result.admission.reasons)


def test_bad_ast_fails_closed_without_partial_output():
    req=make_request(); data=make_response(req); data['program']['node']['kind']='TELEPORT'
    result=GeneralizedIngressR1(OllamaGeneralizedIngressBackend(ref(),Transport(data))).parse(req)
    assert not result.admission.accepted
    assert result.semantic_atoms==() and result.task is None and result.program is None


def test_transport_exception_fails_closed_without_partial_output():
    result=GeneralizedIngressR1(OllamaGeneralizedIngressBackend(ref(),Transport(exc=RuntimeError('offline')))).parse(make_request())
    assert not result.admission.accepted
    assert result.semantic_atoms==() and result.task is None and result.program is None
