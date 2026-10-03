from pathlib import Path
import pytest
from nexus_gllm.unified_runtime.runtime import NexusUnifiedCognitiveRuntime
from nexus_gllm.unified_runtime.v72_cortex import V72CortexAdapter
from nexus_gllm.unified_runtime.learned_meta import LearnedMetaPolicy

CKPT=Path('/mnt/data/nexus_ru_cortex_v7_2_i_curriculum.pt')

def tokenizer_for_wiring(text):
    # Wiring-only tokenizer; not a recovered V7.2 tokenizer provenance claim.
    return [1+(b%1000) for b in text.encode('utf-8')][:112] or [1]

@pytest.mark.skipif(not CKPT.exists(),reason='real checkpoint not mounted')
def test_real_checkpoint_end_to_end_and_observe_changes_policy():
    c=V72CortexAdapter(CKPT,nhead=8); p=LearnedMetaPolicy(seed=9)
    rt=NexusUnifiedCognitiveRuntime(cortex=c,meta_policy=p,tokenizer=tokenizer_for_wiring)
    before=p.parameter_hash(); r=rt.answer('Запомни: ключ проекта = орбита-47.','s',novelty=.7)
    assert 'орбита-47' in r.text
    assert any(x.startswith('cortex=v7.2:') for x in r.trace)
    tel=rt.observe(r.episode_id,observed_reward=1.0,credit=.9)
    assert p.parameter_hash()!=before
    assert 'rpe' in tel
