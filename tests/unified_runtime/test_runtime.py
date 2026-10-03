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
def test_real_checkpoint_end_to_end_crc_credit_changes_policy():
    c=V72CortexAdapter(CKPT,nhead=8); p=LearnedMetaPolicy(seed=9)
    rt=NexusUnifiedCognitiveRuntime(cortex=c,meta_policy=p,tokenizer=tokenizer_for_wiring)
    before=p.parameter_hash()
    r=rt.answer('Запомни: ключ проекта = орбита-47.','s',novelty=.7)
    assert 'орбита-47' in r.text
    assert any(x.startswith('cortex=v7.2:') for x in r.trace)
    assert any(x.startswith('crc_memory=mem:') for x in r.trace)
    assert any(x.startswith('crc_future=root/') for x in r.trace)

    result=rt.observe(r.episode_id,observed_reward=1.0,progress=.2)
    assert p.parameter_hash()!=before
    assert result.crc.rpe != 0.0
    assert result.crc.meta_credit != 0.0
    assert 'learned_meta' in result.crc.credit
    assert 'rpe' in result.policy
    assert result.crc.state.observed_reward is not None
    assert rt.crc.self_model.get('learned_meta_policy').credit_mass != 0.0


@pytest.mark.skipif(not CKPT.exists(),reason='real checkpoint not mounted')
def test_counterfactual_meta_credit_reaches_policy_update():
    c=V72CortexAdapter(CKPT,nhead=8); p=LearnedMetaPolicy(seed=11)
    rt=NexusUnifiedCognitiveRuntime(cortex=c,meta_policy=p,tokenizer=tokenizer_for_wiring)
    r=rt.answer('Нет данных о температуре.','evidence',novelty=.9)
    result=rt.observe(
        r.episode_id,
        observed_reward=-.5,
        contradiction=.2,
        counterfactual_credit={'learned_meta': -.75},
    )
    assert result.crc.meta_credit < 0.0
    assert result.policy['advantage'] != 0.0
