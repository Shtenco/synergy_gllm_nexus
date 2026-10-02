from __future__ import annotations

import hashlib
import json

import pytest

from nexus_gllm.unified_v3.cognitive.generalized_ingress import GeneralizedIngressRequest, GeneralizedIngressR1
from nexus_gllm.unified_v3.cognitive.generalized_ingress_llamacpp import (
    LlamaCppGeneralizedIngressBackend,
    LlamaCppModelRef,
)


class FakeTransport:
    def __init__(self, response=None, error=None):
        self.response=response; self.error=error; self.calls=[]
    def post_json(self,url,payload,timeout_s):
        self.calls.append((url,payload,timeout_s))
        if self.error: raise self.error
        return self.response


def _model(tmp_path, content=b'model-bytes'):
    p=tmp_path/'model.gguf';p.write_bytes(content)
    return p,hashlib.sha256(content).hexdigest()


def _request():
    return GeneralizedIngressRequest.from_texts(
        'Is Alice parent Carol?',
        history=('Alice parent Bob.',),
        documents=('Bob parent Carol.',),
    )


def _json_response():
    request=_request(); prompt=request.source_map['prompt:0']; history=request.source_map['history:0']; document=request.source_map['document:0']
    body={
      'semantic_atoms':[
        {'operator_id':'parent','arguments':['alice','bob'],'polarity':True,'confidence':.95,'spans':[{'source_id':'history:0','start':0,'end':len(history.text)}]},
        {'operator_id':'parent','arguments':['bob','carol'],'polarity':True,'confidence':.95,'spans':[{'source_id':'document:0','start':0,'end':len(document.text)}]},
      ],
      'task':{'opcode':'QUERY_RELATION','operator_id':'parent','arguments':['alice','carol'],'confidence':.95,'spans':[{'source_id':'prompt:0','start':0,'end':len(prompt.text)}]},
      'program':{'confidence':.95,'spans':[{'source_id':'prompt:0','start':0,'end':len(prompt.text)}],'node':{'kind':'ATOM','symbol':'rule:transitive:parent','children':[],'params':[]}},
    }
    return {'choices':[{'message':{'content':json.dumps(body)}}]}


def _typed_ir_response(body):
    return {'choices':[{'message':{'content':json.dumps(body)}}]}


def test_model_bytes_must_match_pinned_sha(tmp_path):
    path,digest=_model(tmp_path)
    bad=LlamaCppModelRef(str(path),'0'*64,'http://127.0.0.1:8080')
    with pytest.raises(ValueError,match='model_sha256_mismatch'):
        LlamaCppGeneralizedIngressBackend(bad,transport=FakeTransport(_json_response()))
    good=LlamaCppModelRef(str(path),digest,'http://127.0.0.1:8080')
    assert LlamaCppGeneralizedIngressBackend(good,transport=FakeTransport(_json_response())).verified_model_sha256==digest


def test_single_call_returns_grounded_semantic_task_and_program(tmp_path):
    path,digest=_model(tmp_path);transport=FakeTransport(_json_response())
    backend=LlamaCppGeneralizedIngressBackend(LlamaCppModelRef(str(path),digest,'http://127.0.0.1:8080'),transport=transport)
    result=GeneralizedIngressR1(backend).parse(_request())
    assert len(transport.calls)==1
    assert result.admission.accepted
    assert len(result.semantic_atoms)==2
    assert result.task is not None
    assert result.program is not None
    payload=transport.calls[0][1]
    assert payload['temperature']==0
    assert payload['seed']==42
    assert payload['response_format']['type']=='json_schema'
    assert 'schema' not in payload['response_format']
    assert payload['response_format']['json_schema']['schema']['additionalProperties'] is False


def test_transport_failure_is_fail_closed(tmp_path):
    path,digest=_model(tmp_path)
    backend=LlamaCppGeneralizedIngressBackend(LlamaCppModelRef(str(path),digest,'http://127.0.0.1:8080'),transport=FakeTransport(error=RuntimeError('offline')))
    result=GeneralizedIngressR1(backend).parse(_request())
    assert not result.admission.accepted
    assert result.semantic_atoms==()
    assert result.task is None and result.program is None


def test_malformed_chat_completion_is_fail_closed(tmp_path):
    path,digest=_model(tmp_path)
    backend=LlamaCppGeneralizedIngressBackend(LlamaCppModelRef(str(path),digest,'http://127.0.0.1:8080'),transport=FakeTransport({'choices':[]}))
    result=GeneralizedIngressR1(backend).parse(_request())
    assert not result.admission.accepted
    assert result.semantic_atoms==()


def test_prompt_contract_spells_out_required_json_shape_and_all_task_opcodes(tmp_path):
    path,digest=_model(tmp_path);transport=FakeTransport(_json_response())
    backend=LlamaCppGeneralizedIngressBackend(
        LlamaCppModelRef(str(path),digest,'http://127.0.0.1:8080'),
        transport=transport,
    )
    GeneralizedIngressR1(backend).parse(_request())
    system=transport.calls[0][1]['messages'][0]['content']
    for required in (
        'semantic_atoms','operator_id','arguments','polarity','confidence',
        'source_ids','task','opcode','program_recipe',
    ):
        assert required in system
    for opcode in (
        'query_relation','select_entity','extract_set','order_tuple','epistemic_status',
        'find_proof','find_minimal_proof','compare_worlds','counterfactual_query',
        'current_state','historical_state',
    ):
        assert opcode in system
    assert 'Never emit top-level summary' in system
    assert '{"semantic_atoms":[],"task":null,"program_recipe":null}' in system


def test_schema_constrains_typed_ir_cardinality_types_and_source_ids(tmp_path):
    path,digest=_model(tmp_path);transport=FakeTransport(_json_response())
    backend=LlamaCppGeneralizedIngressBackend(
        LlamaCppModelRef(str(path),digest,'http://127.0.0.1:8080'),
        transport=transport,
    )
    GeneralizedIngressR1(backend).parse(_request())
    schema=transport.calls[0][1]['response_format']['json_schema']['schema']
    assert schema['required']==['semantic_atoms','task','program_recipe']
    atoms=schema['properties']['semantic_atoms']
    assert atoms['maxItems']==4
    atom=atoms['items']
    assert atom['additionalProperties'] is False
    assert atom['properties']['arguments']['items']=={'type':'string'}
    assert atom['properties']['arguments']['maxItems']==4
    source_ids=atom['properties']['source_ids']
    assert source_ids['items']['enum']==['prompt:0','history:0','document:0']
    assert source_ids['maxItems']==3
    task=schema['properties']['task']['anyOf'][1]
    assert 'query_relation' in task['properties']['opcode']['enum']
    recipe=schema['properties']['program_recipe']['anyOf'][1]
    assert recipe['properties']['kind']['enum']==['transitive','composition','counterfactual_transitive']
    assert recipe['properties']['operators']['maxItems']==3
    assert recipe['properties']['add_fact']['maxItems']==3


def test_typed_ir_compiles_transitive_recipe_and_full_source_provenance(tmp_path):
    path,digest=_model(tmp_path)
    body={
      'semantic_atoms':[
        {'operator_id':'parent','arguments':['alice','bob'],'polarity':True,'confidence':.95,'source_ids':['history:0']},
        {'operator_id':'parent','arguments':['bob','carol'],'polarity':True,'confidence':.95,'source_ids':['document:0']},
      ],
      'task':{'opcode':'query_relation','operator_id':'parent','arguments':['alice','carol'],'confidence':.95,'source_ids':['prompt:0']},
      'program_recipe':{'kind':'transitive','operators':['parent'],'add_fact':[],'confidence':.95,'source_ids':['history:0','document:0']},
    }
    backend=LlamaCppGeneralizedIngressBackend(
        LlamaCppModelRef(str(path),digest,'http://127.0.0.1:8080'),
        transport=FakeTransport(_typed_ir_response(body)),
    )
    result=GeneralizedIngressR1(backend).parse(_request())
    assert result.admission.accepted
    assert result.task is not None
    assert result.program is not None
    assert result.program.node.kind.value=='ATOM'
    assert result.program.node.symbol=='rule:transitive:parent'
    assert {s.source_id for s in result.program.supporting_spans}=={'history:0','document:0'}


def test_typed_ir_compiles_counterfactual_recipe_without_recursive_model_ast(tmp_path):
    path,digest=_model(tmp_path)
    request=GeneralizedIngressRequest.from_texts(
        'If Bob parent Carol, is Alice parent Carol?',
        history=('alice parent bob',),
    )
    body={
      'semantic_atoms':[{'operator_id':'parent','arguments':['alice','bob'],'polarity':True,'confidence':.95,'source_ids':['history:0']}],
      'task':{'opcode':'query_relation','operator_id':'parent','arguments':['alice','carol'],'confidence':.95,'source_ids':['prompt:0']},
      'program_recipe':{
        'kind':'counterfactual_transitive','operators':['parent'],'add_fact':['parent','bob','carol'],
        'confidence':.95,'source_ids':['prompt:0','history:0'],
      },
    }
    backend=LlamaCppGeneralizedIngressBackend(
        LlamaCppModelRef(str(path),digest,'http://127.0.0.1:8080'),
        transport=FakeTransport(_typed_ir_response(body)),
    )
    result=GeneralizedIngressR1(backend).parse(request)
    assert result.admission.accepted
    assert result.program.node.kind.value=='COUNTERFACTUAL'
    assert result.program.node.children[0].symbol=='rule:transitive:parent'
    assert dict(result.program.node.params)=={'kind':'ADD_FACT','operator':'parent','src':'bob','dst':'carol'}


def test_typed_ir_recipe_is_fail_closed_for_unknown_kind_or_source(tmp_path):
    path,digest=_model(tmp_path)
    for recipe in (
        {'kind':'magic','operators':['parent'],'confidence':.95,'source_ids':['prompt:0']},
        {'kind':'transitive','operators':['parent'],'confidence':.95,'source_ids':['missing:9']},
    ):
        body={'semantic_atoms':[],'task':None,'program_recipe':recipe}
        backend=LlamaCppGeneralizedIngressBackend(
            LlamaCppModelRef(str(path),digest,'http://127.0.0.1:8080'),
            transport=FakeTransport(_typed_ir_response(body)),
        )
        result=GeneralizedIngressR1(backend).parse(_request())
        assert not result.admission.accepted
