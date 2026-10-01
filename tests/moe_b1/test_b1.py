from pathlib import Path
from dataclasses import replace
import pytest
from benchmarks.moe_b1.generator import generate_splits
from benchmarks.moe_b1.rollout import ExactExpertFederation,Rollout,EXPERTS
from benchmarks.moe_b1.train_router import train_router
from benchmarks.moe_b1.evaluate import evaluate_strategies,learned_fuse
from benchmarks.moe_b1.seal import seal_b1,verify_sealed
from benchmarks.moe_b1.protocol import run_protocol
HAS_EXTERNAL=Path('/mnt/data/r7_seed711.pt').is_file()
requires_external=pytest.mark.skipif(not HAS_EXTERNAL,reason='external exact-artifact bundle is not mounted on this host')
def test_b1_splits_are_disjoint_and_router_features_have_no_family_or_gold():
    s=generate_splits(seed=6101,train_per_family=12,dev_per_family=4,test_per_family=5);ids=[set(x.case_id for x in s[k]) for k in ('train','dev','test')];assert ids[0].isdisjoint(ids[1]) and ids[0].isdisjoint(ids[2]) and ids[1].isdisjoint(ids[2]);f=s['train'][0].router_features();assert not ({'family','gold','split','case_id'}&set(f))
@requires_external
def test_b1_real_rollouts_and_learned_moe_gain(tmp_path):
    s=generate_splits(seed=6102,train_per_family=30,dev_per_family=8,test_per_family=12);fed=ExactExpertFederation(Path('/mnt/data'));train=fed.rollout_many(s['train']);dev=fed.rollout_many(s['dev']);test=fed.rollout_many(s['test']);model=train_router(train,dev,seed=17,epochs=45);result=evaluate_strategies(test,model)
    assert result['oracle']['accuracy']>=result['learned_moe']['accuracy'];assert result['oracle']['negative_transfer_rate']==0.0;assert result['oracle']['accuracy']-result['learned_moe']['accuracy']<=0.10;assert result['learned_moe']['accuracy']>result['best_single']['accuracy']+0.10;assert result['learned_moe']['negative_transfer_rate']<=0.05
def test_b1_seal_hashes_test_before_evaluation(tmp_path):
    s=generate_splits(seed=6103,train_per_family=4,dev_per_family=2,test_per_family=3);m=seal_b1(tmp_path,s,artifact_manifest_sha256='a'*64);assert m['sealed_before_evaluation'] and verify_sealed(tmp_path,s)
@requires_external
def test_rollout_does_not_mutate_sealed_cases(tmp_path):
    s=generate_splits(seed=6104,train_per_family=3,dev_per_family=2,test_per_family=3);seal_b1(tmp_path,s,artifact_manifest_sha256='b'*64);ExactExpertFederation(Path('/mnt/data')).rollout_many(s['test']);assert verify_sealed(tmp_path,s)
@requires_external
def test_evidence_inputs_are_sealed_and_rollout_does_not_read_gold_for_teacher_rows():
    s=generate_splits(seed=6110,train_per_family=2,dev_per_family=1,test_per_family=2);case=next(c for c in s['test'] if c.family=='evidence_credit');fed=ExactExpertFederation(Path('/mnt/data'));a=fed.rollout(case).answers['r718'];b=fed.rollout(replace(case,gold='__SCORER_ONLY_SENTINEL__')).answers['r718'];assert a==b
def test_learned_fusion_uses_router_utility_and_lineage_not_raw_majority():
    case=next(iter(generate_splits(seed=6111,train_per_family=1,dev_per_family=1,test_per_family=1)['test']));answers={e:None for e in EXPERTS};answers['r7l']='WRONG';answers['r72']='WRONG';answers['r76']='RIGHT';assert learned_fuse(Rollout(case,answers),[0,1,2],[0.15,0.15,2.0,-1,-1,-1,-1])=='RIGHT'
def test_evidence_credit_gold_is_supported_by_four_of_five_sealed_teachers():
    for c in [c for c in generate_splits(seed=6112,train_per_family=20,dev_per_family=2,test_per_family=2)['train'] if c.family=='evidence_credit']:assert sum(row['pred']==c.gold for row in c.payload['teacher_rows'].values())==4
def test_evidence_credit_single_distractor_is_explicitly_low_confidence():
    for c in [c for c in generate_splits(seed=6113,train_per_family=6,dev_per_family=1,test_per_family=1)['train'] if c.family=='evidence_credit']:
        d=[row for row in c.payload['teacher_rows'].values() if row['pred']!=c.gold];assert len(d)==1 and d[0]['option_logprobs'][d[0]['pred']]<=-2.5
@requires_external
def test_protocol_freezes_artifacts_router_and_test_before_one_shot_result(tmp_path):
    out=run_protocol(tmp_path,Path('/mnt/data'),seed=6201,train_per_family=2,dev_per_family=1,test_per_family=1,router_seed=17,epochs=5);assert out['protocol']['test_open_count']==1 and out['protocol']['tuning_after_test_open'] is False
def test_fast_ru_uses_broad_blind20_surface_family_not_one_query_template():
    cases=[c for c in generate_splits(seed=6114,train_per_family=30,dev_per_family=2,test_per_family=2)['train'] if c.family=='fast_ru'];surfaces=set()
    for c in cases:
        t=c.text
        for state in ('янтарь','лазурь','графит','нефрит'):t=t.replace(f'«{state}»','«STATE»')
        surfaces.add(t)
    assert len(surfaces)>=6
