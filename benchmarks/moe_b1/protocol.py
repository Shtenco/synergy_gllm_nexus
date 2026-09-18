from __future__ import annotations
from pathlib import Path
import hashlib,json,torch
from nexus_gllm.unified_v3.moe.exact_artifacts import ArtifactCatalog
from .generator import generate_splits
from .rollout import ExactExpertFederation,EXPERTS
from .train_router import train_router
from .evaluate import evaluate_strategies
from .seal import seal_b1,verify_sealed

def _sha(path:Path)->str:return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _logical_state_hash(model)->str:
    h=hashlib.sha256()
    for k,v in sorted(model.state_dict().items()):h.update(k.encode());h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()
def _artifact_manifest(root:Path)->dict:
    cat=ArtifactCatalog.default(root);rows=[]
    for eid in cat.records:
        rec=cat.verify(eid);files=[]
        for rel,expected in zip(rec.paths,rec.expected_sha256):
            p=Path(root)/rel;files.append({'name':rel,'expected_sha256':expected,'actual_sha256':_sha(p) if p.is_file() else None,'bytes':p.stat().st_size if p.is_file() else None})
        rows.append({'expert_id':eid,'status':rec.status.value,'files':files,'notes':rec.notes})
    return {'name':'NEXUS v3-MoE Artifact-Complete Audit','date':'2026-09-19','exact_runnable_experts':[r['expert_id'] for r in rows if r['status']=='EXACT_RUNNABLE'],'records':rows,'scientific_boundary':'Only EXACT_RUNNABLE experts execute in NEXUS-MOE-B1. Missing binaries/dependencies remain fail-closed and are not silently reconstructed as exact.'}
def run_protocol(outdir:Path,artifact_root:Path,seed:int=2026091907,train_per_family:int=300,dev_per_family:int=75,test_per_family:int=150,router_seed:int=17,epochs:int=45):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True);artifact_manifest=_artifact_manifest(Path(artifact_root));artifact_path=out/'ARTIFACT_COMPLETE_MANIFEST.json';artifact_path.write_text(json.dumps(artifact_manifest,indent=2,sort_keys=True,ensure_ascii=False),encoding='utf-8');artifact_sha=_sha(artifact_path)
    splits=generate_splits(seed=seed,train_per_family=train_per_family,dev_per_family=dev_per_family,test_per_family=test_per_family);freeze=seal_b1(out,splits,artifact_sha)
    if not verify_sealed(out,splits):raise RuntimeError('B1 split seal verification failed before training')
    federation=ExactExpertFederation(Path(artifact_root));train_rollouts=federation.rollout_many(splits['train']);dev_rollouts=federation.rollout_many(splits['dev']);model=train_router(train_rollouts,dev_rollouts,seed=router_seed,epochs=epochs)
    router_path=out/'router_b1.pt';torch.save(model.state_dict(),router_path);dev_metrics=evaluate_strategies(dev_rollouts,model)
    pretest={'name':'NEXUS-MOE-B1 PRETEST MODEL FREEZE','date':'2026-09-19','benchmark_seed':seed,'counts':freeze['counts'],'test_split_sha256':freeze['split_sha256']['test'],'artifact_manifest_sha256':artifact_sha,'router_seed':router_seed,'router_epochs':epochs,'router_serialized_sha256':_sha(router_path),'router_logical_sha256':_logical_state_hash(model),'experts':list(EXPERTS),'dev_metrics':dev_metrics,'test_metrics':None,'test_opened':False,'tuning_after_test_open':False}
    pretest_path=out/'NEXUS_MOE_B1_PRETEST_MODEL_FREEZE.json';pretest_path.write_text(json.dumps(pretest,indent=2,sort_keys=True,ensure_ascii=False),encoding='utf-8')
    if not verify_sealed(out,splits):raise RuntimeError('B1 split seal changed before one-shot evaluation')
    result=evaluate_strategies(federation.rollout_many(splits['test']),model)
    protocol={'sealed_before_evaluation':True,'pretest_model_freeze_sha256':_sha(pretest_path),'test_open_count':1,'tuning_after_test_open':False,'ftx1_blind_used':False,'hard_oos_d_reused_as_oos':False}
    payload={'benchmark':'NEXUS-MOE-B1','result':result,'protocol':protocol};(out/'NEXUS_MOE_B1_ONE_SHOT_RESULT.json').write_text(json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False),encoding='utf-8');return payload
