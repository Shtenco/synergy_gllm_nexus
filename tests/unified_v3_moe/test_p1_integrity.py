import json
from pathlib import Path
import pytest,torch
from nexus_gllm.unified_v3.moe.integrity import generate_integrity_manifest,validate_torch_payloads
from nexus_gllm.unified_v3.moe.learned_router import _RouterNet,_NoveltyNet,_Calibrator,P1_EXPERTS,P1_FEATURES

def fixture(root:Path):
    torch.manual_seed(17)
    torch.save(_RouterNet().state_dict(),root/'router.pt')
    torch.save(_NoveltyNet().state_dict(),root/'novelty.pt')
    torch.save(_Calibrator().state_dict(),root/'calibrator.pt')
    (root/'manifest.json').write_text(json.dumps({'experts':list(P1_EXPERTS),'features':list(P1_FEATURES)}))
    (root/'metrics.json').write_text('{}')

def test_integrity_requires_torch_loadability_not_only_sha(tmp_path):
    fixture(tmp_path);m=generate_integrity_manifest(tmp_path,source_commit='abc')
    assert m['format_version']==2 and all(m['loadability'].values())
    (tmp_path/'router.pt').write_bytes(b'not-a-checkpoint')
    with pytest.raises(RuntimeError,match='router.pt is not a loadable frozen checkpoint'):
        generate_integrity_manifest(tmp_path,source_commit='abc')

def test_recovery_logical_hash_is_enforced(tmp_path):
    fixture(tmp_path);m=generate_integrity_manifest(tmp_path)
    expected=dict(m['logical_state_sha256']);expected['router.pt']='0'*64
    (tmp_path/'recovery.json').write_text(json.dumps({'logical_state_sha256':expected}))
    with pytest.raises(RuntimeError,match='logical state hash mismatch'):
        validate_torch_payloads(tmp_path)
