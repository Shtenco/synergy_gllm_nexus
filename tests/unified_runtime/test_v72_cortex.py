from pathlib import Path
import hashlib
import pytest
import torch

from nexus_gllm.unified_runtime.v72_cortex import V72CortexAdapter, EXPECTED_SHA256, _RecoveredV72

CKPT = Path('/mnt/data/nexus_ru_cortex_v7_2_i_curriculum.pt')


def test_synthetic_state_dict_contract_in_ci(tmp_path):
    path=tmp_path/'synthetic_v72.pt'
    model=_RecoveredV72(nhead=8)
    torch.save({'state_dict':model.state_dict(),'meta':{'name':'synthetic-contract-only'}},path)
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    a=V72CortexAdapter(path,expected_sha256=sha,nhead=8)
    x=a.infer_token_ids([1,2,3])
    assert (len(x.plan_probs),len(x.relation_probs),len(x.role_probs),len(x.temporal_probs))==(14,2,8,3)

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
