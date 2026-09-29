from benchmarks.crc_meta_g.generator import generate,STRATA
from benchmarks.crc_meta_g.runner import decide
from benchmarks.crc_meta_g.scorer import score
from benchmarks.crc_meta_g.seal import seal,verify

def test_runtime_has_no_gold_or_reward():
    c=generate(seed=1,n_per_stratum=1).runtime[0]
    assert not hasattr(c,'execution_truth') and not hasattr(c,'first_action') and not hasattr(c,'observed_task_reward')

def test_all_integrated_strata_present():
    b=generate(seed=2,n_per_stratum=2);assert {c.stratum for c in b.runtime}==set(STRATA)

def test_decision_builds_complete_crc_trace():
    c=generate(seed=3,n_per_stratum=1).runtime[0];_,_,p=decide(c)
    assert {'meta','memory','program','branch','answer'}.issubset(set(p.trace_kinds))

def test_meta_g_scoring_is_component_explicit():
    b=generate(seed=4,n_per_stratum=2);preds=tuple(decide(c)[2] for c in b.runtime);s=score(b.runtime,b.gold,preds)
    assert set(('strict_integrated_accuracy','execution_accuracy','planning_accuracy','memory_retrieval_success','trace_completeness')).issubset(s)

def test_seal_detects_runtime_mutation(tmp_path):
    b=generate(seed=5,n_per_stratum=1);seal(tmp_path,b,'a'*64);assert verify(tmp_path);p=tmp_path/'runtime.jsonl';p.write_text(p.read_text()+'x');assert not verify(tmp_path)
