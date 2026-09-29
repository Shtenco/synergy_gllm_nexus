import json,hashlib
from pathlib import Path
import torch
from nexus_gllm.unified_v3.moe.learned_router import LoadableCapabilityRouter,_RouterNet,_Calibrator,_NoveltyNet,P1_EXPERTS,P1_FEATURES,P1_PAYLOAD_FILES
from nexus_gllm.unified_v3.moe.integrity import generate_integrity_manifest
def fixture(tmp_path):
    torch.manual_seed(1);torch.save(_RouterNet().state_dict(),tmp_path/'router.pt');torch.save(_NoveltyNet().state_dict(),tmp_path/'novelty.pt');torch.save(_Calibrator().state_dict(),tmp_path/'calibrator.pt')
    (tmp_path/'manifest.json').write_text(json.dumps({'experts':list(P1_EXPERTS),'features':list(P1_FEATURES)}));(tmp_path/'metrics.json').write_text('{}');generate_integrity_manifest(tmp_path,source_commit='test');return tmp_path
def test_default_hash_verification_requires_integrity_manifest(tmp_path):
    fixture(tmp_path);(tmp_path/'integrity.sha256.json').unlink();r=LoadableCapabilityRouter(tmp_path);assert not r.status.loaded and r.status.reason=='integrity_manifest_missing'
def test_generated_integrity_manifest_enables_loading(tmp_path):
    fixture(tmp_path);r=LoadableCapabilityRouter(tmp_path);assert r.status.loaded and r.status.integrity_source=='committed_manifest'
def test_tamper_fails_closed(tmp_path):
    fixture(tmp_path);p=tmp_path/'metrics.json';p.write_text('{"tampered":true}');r=LoadableCapabilityRouter(tmp_path);assert not r.status.loaded and 'sha256_mismatch' in r.status.reason
