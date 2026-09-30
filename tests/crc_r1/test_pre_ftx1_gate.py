import json
from nexus_gllm.unified_v3.cognitive.pre_ftx1 import PreFTX1FreezeGate
def ready():
    g=PreFTX1FreezeGate()
    return {'schema':g.REQUIRED_SCHEMA,'commit':'abc','gates':{k:True for k in g.REQUIRED_GATES},'ready_for_pre_ftx1_freeze':True,'ftx1_used':False,'hard_oos_d_reused_as_clean_oos':False}
def test_gate_denies_missing_evidence(tmp_path):
    assert not PreFTX1FreezeGate().decide(tmp_path/'missing.json').allowed
def test_gate_denies_v2_schema_even_if_gates_are_true(tmp_path):
    m=ready();m['schema']='nexus.crc_r1.validation.v2';p=tmp_path/'e.json';p.write_text(json.dumps(m));d=PreFTX1FreezeGate().decide(p);assert not d.allowed and 'validation_schema_mismatch' in d.reasons
def test_gate_denies_any_failed_gate(tmp_path):
    m=ready();m['gates']['meta_g_strict_ge_090']=False;p=tmp_path/'e.json';p.write_text(json.dumps(m));assert not PreFTX1FreezeGate().decide(p).allowed
def test_freeze_never_opens_ftx1(tmp_path):
    m=ready();p=tmp_path/'e.json';p.write_text(json.dumps(m));out=tmp_path/'freeze.json';f=PreFTX1FreezeGate().freeze(p,out,commit='abc');assert f['status']=='FROZEN_PRE_FTX1' and f['ftx1_opened'] is False


def test_freeze_rejects_green_evidence_from_different_commit(tmp_path):
    m=ready();m['commit']='old';p=tmp_path/'e.json';p.write_text(json.dumps(m));out=tmp_path/'freeze.json'
    try:PreFTX1FreezeGate().freeze(p,out,commit='new')
    except RuntimeError as e:
        assert 'evidence_commit_mismatch' in str(e);return
    assert False

def test_freeze_binds_evidence_and_code_commit(tmp_path):
    m=ready();p=tmp_path/'e.json';p.write_text(json.dumps(m));out=tmp_path/'freeze.json'
    f=PreFTX1FreezeGate().freeze(p,out,commit='abc')
    assert f['commit']==f['evidence_commit']=='abc'
