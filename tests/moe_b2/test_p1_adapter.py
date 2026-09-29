import json,torch
from benchmarks.moe_b2.generator import generate
from benchmarks.moe_b2.p1_adapter import FrozenP1B2Adapter
from nexus_gllm.unified_v3.moe.learned_router import _RouterNet,_NoveltyNet,_Calibrator,P1_EXPERTS,P1_FEATURES
from nexus_gllm.unified_v3.moe.integrity import generate_integrity_manifest
def fixture(tmp_path):
    torch.manual_seed(5);torch.save(_RouterNet().state_dict(),tmp_path/'router.pt');torch.save(_NoveltyNet().state_dict(),tmp_path/'novelty.pt');torch.save(_Calibrator().state_dict(),tmp_path/'calibrator.pt');(tmp_path/'manifest.json').write_text(json.dumps({'experts':list(P1_EXPERTS),'features':list(P1_FEATURES)}));(tmp_path/'metrics.json').write_text('{}');generate_integrity_manifest(tmp_path);return tmp_path
def test_adapter_accepts_runtime_case_only(tmp_path):
    a=FrozenP1B2Adapter(fixture(tmp_path));c=generate(seed=8,n_per_stratum=1).runtime[0];r=a.route(c);assert 2<=len(r.selected)<=4
def test_adapter_preserves_continuous_b2_signals(tmp_path):
    a=FrozenP1B2Adapter(fixture(tmp_path));c=generate(seed=9,n_per_stratum=1).runtime[0];f=a._features(c);x=dict(zip(('support','ru','evidence','context','graph','novelty','proof','cost'),c.features));assert abs(f.ru_signal-x['ru'])<1e-12 and abs(f.evidence_signal-x['evidence'])<1e-12
