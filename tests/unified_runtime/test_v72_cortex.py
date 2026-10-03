from pathlib import Path
import pytest

from nexus_gllm.unified_runtime.v72_cortex import V72CortexAdapter, EXPECTED_SHA256

CKPT = Path('/mnt/data/nexus_ru_cortex_v7_2_i_curriculum.pt')

@pytest.mark.skipif(not CKPT.exists(), reason='real checkpoint not mounted')
def test_real_checkpoint_dimensions_and_determinism():
    a = V72CortexAdapter(CKPT, nhead=8)
    x1 = a.infer_token_ids([1,2,3,4,5])
    x2 = a.infer_token_ids([1,2,3,4,5])
    assert len(x1.plan_probs)==14
    assert len(x1.relation_probs)==2
    assert len(x1.role_probs)==8
    assert len(x1.temporal_probs)==3
    assert x1==x2
    assert x1.checkpoint_sha256==EXPECTED_SHA256
    assert x1.reconstruction_exact_source is False

@pytest.mark.skipif(not CKPT.exists(), reason='real checkpoint not mounted')
def test_wrong_hash_fails_closed():
    with pytest.raises(ValueError, match='SHA-256 mismatch'):
        V72CortexAdapter(CKPT, expected_sha256='0'*64)
