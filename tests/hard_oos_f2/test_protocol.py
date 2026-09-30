from benchmarks.hard_oos_f2.generator import generate,STRATA
from benchmarks.hard_oos_f2.runner import crc_predict,fixed_basis_predict
from benchmarks.hard_oos_f2.scorer import score
from benchmarks.hard_oos_f2.seal import seal,verify

def test_gold_is_quarantined():
    b=generate(seed=1,n_per_stratum=2);assert not hasattr(b.runtime[0],'expected_truth') and not hasattr(b.runtime[0],'expected_status')
def test_all_negative_strata_present():
    b=generate(seed=2,n_per_stratum=3);assert {x.stratum for x in b.runtime}==set(STRATA)
def test_fixed_basis_cannot_represent_higher_order_negative_semantics():
    b=generate(seed=3,n_per_stratum=2);s=score(b.runtime,b.gold,tuple(fixed_basis_predict(c) for c in b.runtime));assert s['representation_failure_rate']==1.0
def test_crc_executes_all_preregistered_negative_semantics():
    b=generate(seed=4,n_per_stratum=8);s=score(b.runtime,b.gold,tuple(crc_predict(c) for c in b.runtime));assert s['representation_failure_rate']==0.0 and s['strict_accuracy']==1.0
def test_seal_detects_runtime_mutation(tmp_path):
    b=generate(seed=5,n_per_stratum=2);seal(tmp_path,b,'a'*64);assert verify(tmp_path);p=tmp_path/'runtime.jsonl';p.write_text(p.read_text()+'x');assert not verify(tmp_path)
