from benchmarks.hard_oos_f.generator import generate,STRATA
from benchmarks.hard_oos_f.runner import crc_predict,fixed_basis_predict
from benchmarks.hard_oos_f.scorer import score
from benchmarks.hard_oos_f.seal import seal,verify
def test_runtime_quarantines_gold_fields():
    b=generate(seed=1,n_per_stratum=3);r=b.runtime[0];assert not hasattr(r,'expected_status') and not hasattr(r,'expected_truth') and not hasattr(r,'topology_sha256')
def test_all_strata_present_and_unique_ids():
    b=generate(seed=2,n_per_stratum=4);assert {r.stratum for r in b.runtime}==set(STRATA);assert len({r.case_id for r in b.runtime})==len(b.runtime)
def test_fixed_basis_reports_representation_failure():
    b=generate(seed=3,n_per_stratum=2);p=tuple(fixed_basis_predict(c) for c in b.runtime);s=score(b.runtime,b.gold,p);assert s['representation_failure_rate']==1.0
def test_crc_executes_positive_higher_order_strata():
    b=generate(seed=4,n_per_stratum=8);p=tuple(crc_predict(c) for c in b.runtime);s=score(b.runtime,b.gold,p);assert s['representation_failure_rate']==0.0;assert s['strict_accuracy']>.45
def test_freeze_detects_mutation(tmp_path):
    b=generate(seed=5,n_per_stratum=2);seal(tmp_path,b,'a'*64);assert verify(tmp_path);p=tmp_path/'runtime.jsonl';p.write_text(p.read_text()+'x');assert not verify(tmp_path)
