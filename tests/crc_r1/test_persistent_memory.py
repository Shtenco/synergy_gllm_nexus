from nexus_gllm.unified_v3.cognitive.persistent_memory import PersistentMemoryIndex
from benchmarks.memory_m5.generator import generate
from benchmarks.memory_m5.runner import hierarchical_predict,flat_predict
from benchmarks.memory_m5.scorer import score
def test_revision_preserves_both_raw_sources():
    m=PersistentMemoryIndex();m.upsert('k','old',evidence='e1');m.upsert('k','new',evidence='e2');assert m.current('k').value=='new';assert [x.active for x in m.history('k')]==[False,True];assert len(m.evidence('k'))==2;assert m.audit()==()
def test_hierarchical_survives_long_distractor_gap():
    c=generate(seed=1,n=1,distractors=80)[0];assert hierarchical_predict(c).value==c.gold_value
def test_flat_small_window_forgets_but_hierarchical_does_not():
    cases=generate(seed=2,n=20,distractors=80);h=score(cases,tuple(hierarchical_predict(c) for c in cases));f=score(cases,tuple(flat_predict(c,32) for c in cases));assert h['current_value_accuracy']>=f['current_value_accuracy'];assert h['raw_provenance_success']==1.0
