import json
from nexus_gllm.unified_v3.cognitive.pre_ftx1 import PreFTX1FreezeGate
def ready():
    g=PreFTX1FreezeGate();return {'gates':{k:True for k in g.REQUIRED_GATES},'ready_for_pre_ftx1_freeze':True,'ftx1_used':False,'hard_oos_d_reused_as_clean_oos':False}
def test_gate_denies_missing_evidence(tmp_path):
    d=PreFTX1FreezeGate().decide(tmp_path/'missing.json');assert not d.allowed
def test_gate_denies_any_failed_gate(tmp_path):
    m=ready();m['gates']['future_gain_nonnegative']=False;p=tmp_path/'e.json';p.write_text(json.dumps(m));d=PreFTX1FreezeGate().decide(p);assert not d.allowed and 'gate_failed:future_gain_nonnegative' in d.reasons
def test_gate_denies_ftx1_boundary_violation(tmp_path):
    m=ready();m['ftx1_used']=True;p=tmp_path/'e.json';p.write_text(json.dumps(m));assert not PreFTX1FreezeGate().decide(p).allowed
def test_freeze_never_opens_ftx1(tmp_path):
    m=ready();p=tmp_path/'e.json';p.write_text(json.dumps(m));out=tmp_path/'freeze.json';f=PreFTX1FreezeGate().freeze(p,out,commit='abc');assert f['status']=='FROZEN_PRE_FTX1' and f['ftx1_opened'] is False
