from __future__ import annotations
import hashlib
import json
from pathlib import Path

from nexus_gllm.unified_v2.preblind_runtime import UnifiedNexusV2Preblind, UnifiedV2Config
from benchmarks.run_unified_v2_ub1 import calculate_score, promotion_gates


def _rows(path: Path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]

def _sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _basic(out):
    n=len(out); correct=sum(int(x['correct']) for x in out)
    return {'n':n,'answered':n,'correct':correct,'coverage':1.0,'strict':correct/n,'precision_answered':correct/n}

def run(bench: Path, workspace_root: Path) -> dict:
    bench=Path(bench); workspace_root=Path(workspace_root)
    rt=UnifiedNexusV2Preblind(UnifiedV2Config.local_default(workspace_root))
    details={}; tracks={}

    out=[]
    for item in _rows(bench/'formal_mcq.jsonl'):
        pred=rt.answer_formal_mcq(item); out.append({'id':item['id'],'answer':pred.answer,'gold':item['gold'],'correct':pred.answer==item['gold'],'stage':pred.stage})
    tracks['formal_mcq']=_basic(out); details['formal_mcq']=out

    out=[]
    for item in _rows(bench/'semantic_mcq.jsonl'):
        pred=rt.answer_semantic_mcq(item); out.append({'id':item['id'],'answer':pred.answer,'gold':item['gold'],'correct':pred.answer==item['gold'],'stage':pred.stage,'source':pred.source})
    tracks['semantic_mcq']=_basic(out); tracks['semantic_mcq']['supplement_used']=sum(x['source']=='Unified-v2 SemanticSupplement' for x in out); details['semantic_mcq']=out

    out=[]
    for item in _rows(bench/'operator_transfer_ru.jsonl'):
        answer=rt.solve_operator_case(item); out.append({'id':item['id'],'answer':answer,'gold':item['gold'],'correct':answer==item['gold']})
    tracks['operator_transfer_ru']=_basic(out); details['operator_transfer_ru']=out

    out=[]
    for item in _rows(bench/'relation_binding_ru.jsonl'):
        pred=rt.parse_relation_roles(item['text']); rel_ok=pred.relation==item['relation']
        if item['relation']=='abstain': strict=rel_ok and pred.subject is None and pred.object is None
        else: strict=rel_ok and pred.subject==item['subject'] and pred.object==item['object']
        out.append({'id':item['id'],'pred_relation':pred.relation,'pred_subject':pred.subject,'pred_object':pred.object,'strict':strict,'relation_correct':rel_ok})
    correct=sum(int(x['strict']) for x in out); n=len(out)
    tracks['relation_binding_ru']={'n':n,'answered':n,'correct':correct,'coverage':1.0,'strict':correct/n,'relation_accuracy':sum(int(x['relation_correct']) for x in out)/n}; details['relation_binding_ru']=out

    out=[]
    for item in _rows(bench/'graph_far_transfer.jsonl'):
        pred=rt.resolve_graph_case(item); answer=pred.get('object'); expected=item['query'][2]
        out.append({'id':item['id'],'answer':answer,'gold':expected,'correct':answer==expected})
    tracks['graph_far_transfer']=_basic(out); details['graph_far_transfer']=out

    out=[]
    for item in _rows(bench/'context_revision.jsonl'):
        answer=rt.resolve_context_case(item); out.append({'id':item['id'],'answer':answer,'gold':item['gold'],'correct':answer==item['gold']})
    tracks['context_revision']=_basic(out); details['context_revision']=out

    out=[]
    for item in _rows(bench/'evidence_trust.jsonl'):
        answer=rt.resolve_evidence_case(item); out.append({'id':item['id'],'answer':answer,'gold':item['gold'],'correct':answer==item['gold']})
    tracks['evidence_trust']=_basic(out); details['evidence_trust']=out

    score=calculate_score(tracks); gates=promotion_gates(tracks,score)
    return {
        'model':'NEXUS Unified v2-PREBLIND',
        'status':'PREBLIND_DEVELOPMENT',
        'protocol_status':'UB1_EXPOSED_DEVELOPMENT',
        'scientific_note':'All 970 UB1 cases execute through one twelve-slot runtime. Semantic supplement was designed after UB1 inspection; UB1 therefore remains development/regression evidence, not blind evidence.',
        'runtime':{'organ_count':len(rt.organ_status),'organ_status':rt.organ_status},
        'tracks':tracks,
        'score':score,
        'promotion_gates_ub1_development':gates,
        'provenance':{
            'ub1_manifest_sha256':_sha(bench/'NEXUS_UB1_FREEZE_MANIFEST.json'),
            'r78_sha256':rt.formal.artifact_sha256,
            'r718_sha256':rt.evidence.artifact_sha256,
            'r72_core_sha256':rt.russian_binder.core_sha256,
            'r72_binder_sha256':rt.russian_binder.binder_sha256,
            'r714_source_sha256':rt.morpholex.source_sha256,
            'r714_model_sha256':rt.morpholex.model_sha256,
            'omega15r2_semantic_sha256':rt.role.semantic_sha256,
            'omega15r2_joint_sha256':rt.role.joint_sha256,
            'r7l_checkpoint_sha256':rt.unseen.checkpoint_sha256,
            'r717_runtime_sha256':rt.recurrent.runtime_sha256,
            'r717_critic_sha256':rt.recurrent.critic_sha256,
            'omega16_source_commit':rt.research.source_commit,
            'unified_v1_runtime_sha256':rt.unified.runtime_sha256,
            'unified_v1_context_sha256':rt.unified.identity.context_sha256,
            'context_source_status':rt.context.source_status,
        },
        'details':details,
    }

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--bench',type=Path,required=True); ap.add_argument('--workspace-root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    result=run(a.bench,a.workspace_root); a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'score':result['score'],'tracks':result['tracks'],'gates':result['promotion_gates_ub1_development']},ensure_ascii=False,indent=2))
