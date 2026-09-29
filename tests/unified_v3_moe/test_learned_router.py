import hashlib,json
from pathlib import Path
import torch
from nexus_gllm.unified_v3.moe.learned_router import LoadableCapabilityRouter,_RouterNet,_Calibrator,_NoveltyNet,P1_EXPERTS,P1_FEATURES
from nexus_gllm.unified_v3.moe.capability_router import RouterFeatures
from nexus_gllm.unified_v3.moe.registry_defaults import build_default_registry

def _sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _fixture(tmp_path):
    torch.manual_seed(3);r=_RouterNet();c=_Calibrator();n=_NoveltyNet();torch.save(r.state_dict(),tmp_path/'router.pt');torch.save(c.state_dict(),tmp_path/'calibrator.pt');torch.save(n.state_dict(),tmp_path/'novelty.pt')
    (tmp_path/'manifest.json').write_text(json.dumps({'experts':list(P1_EXPERTS),'features':list(P1_FEATURES)}),encoding='utf-8');(tmp_path/'metrics.json').write_text('{}',encoding='utf-8')
    return {name:_sha(tmp_path/name) for name in ('router.pt','calibrator.pt','novelty.pt','manifest.json','metrics.json')}

def test_verified_learned_router_loads_and_routes(tmp_path):
    hashes=_fixture(tmp_path); router=LoadableCapabilityRouter(tmp_path,expected_sha256=hashes)
    assert router.status.loaded and router.status.source=='learned_p1'
    d=router.route(RouterFeatures(support_count=4,language='ru',novelty=.9),build_default_registry(),2,4)
    assert 2<=len(d.selected_experts)<=4 and set(d.selected_experts).issubset(set(P1_EXPERTS))

def test_hash_mismatch_fails_closed_to_heuristic(tmp_path):
    hashes=_fixture(tmp_path); hashes['router.pt']='0'*64; router=LoadableCapabilityRouter(tmp_path,expected_sha256=hashes)
    assert not router.status.loaded and router.status.source=='heuristic_fallback' and 'sha256_mismatch' in router.status.reason
    d=router.route(RouterFeatures(support_count=3,language='ru'),build_default_registry(),2,4)
    assert 'r7l' in d.selected_experts and 'r72' in d.selected_experts

def test_manifest_mismatch_fails_closed(tmp_path):
    hashes=_fixture(tmp_path); (tmp_path/'manifest.json').write_text(json.dumps({'experts':['bad'],'features':list(P1_FEATURES)}),encoding='utf-8'); hashes['manifest.json']=_sha(tmp_path/'manifest.json')
    router=LoadableCapabilityRouter(tmp_path,expected_sha256=hashes); assert not router.status.loaded and router.status.reason=='manifest_expert_mismatch'

def test_feature_mapping_is_bounded():
    x=LoadableCapabilityRouter.feature_vector(RouterFeatures(support_count=99,language='ru',evidence_conflict=True,context_depth=99,graph_signal=4,proof_signal=-1,novelty=2,cost_signal=5))
    assert len(x)==8 and all(0<=z<=1 for z in x) and x[0]==1 and x[1]==1 and x[6]==0
