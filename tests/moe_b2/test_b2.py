from benchmarks.moe_b2.generator import generate,FEATURES,STRATA,EXPERTS
from benchmarks.moe_b2.seal import seal,verify
from benchmarks.moe_b2.evaluate import Route,score,oracle_routes,random_routes
from benchmarks.moe_b2.protocol import run_one_shot
def test_runtime_contains_no_scorer_only_fields():
    b=generate(seed=11,n_per_stratum=8);c=b.runtime[0];assert set(c.__dict__)=={'case_id','features','stratum'} and len(c.features)==len(FEATURES);assert not hasattr(c,'useful') and not hasattr(c,'utility')
def test_all_far_oos_strata_present_and_disjoint_ids():
    b=generate(seed=12,n_per_stratum=9);assert {c.stratum for c in b.runtime}==set(STRATA);assert len({c.case_id for c in b.runtime})==len(b.runtime)
def test_seal_detects_mutation(tmp_path):
    b=generate(seed=13,n_per_stratum=3);seal(tmp_path,b,'a'*64);assert verify(tmp_path);p=tmp_path/'runtime.jsonl';p.write_text(p.read_text()+'x');assert not verify(tmp_path)
def test_oracle_dominates_random_on_regret():
    b=generate(seed=14,n_per_stratum=30);o=score(b.runtime,b.gold,oracle_routes(b.runtime,b.gold));r=score(b.runtime,b.gold,random_routes(b.runtime,5));assert o['overall']['mean_routing_regret']<=r['overall']['mean_routing_regret'];assert o['overall']['harmful_selection_rate']<=r['overall']['harmful_selection_rate']
def test_one_shot_protocol_routes_before_scoring(tmp_path):
    def route(c):return Route((EXPERTS[0],EXPERTS[1],EXPERTS[2]))
    x=run_one_shot(tmp_path,route,seed=15,n_per_stratum=3,source_sha256='b'*64);assert x['protocol']['test_open_count']==1 and x['protocol']['tuning_after_open'] is False and verify(tmp_path)
