from __future__ import annotations
from pathlib import Path
import hashlib,json,os

def _load(p):return json.loads(Path(p).read_text())

def build(root,*,commit=None):
    root=Path(root)
    b2=_load(root/'b2'/'one_shot_result.json')
    hf=_load(root/'hard_oos_f'/'one_shot_result.json')
    hf2=_load(root/'hard_oos_f2'/'one_shot_result.json')
    meta=_load(root/'meta_g'/'one_shot_result.json')
    m8=_load(root/'m8_ablation.json')
    causal=_load(root/'causal_m15.json')
    info=_load(root/'info_gain_m16.json')
    program=_load(root/'program_m25.json')
    integrity=_load(root/'p1_integrity.sha256.json')

    gates={}
    lb=b2['learned_or_candidate']['overall'];rb=b2['random']['overall']
    gates['b2_beats_random_recall']=lb['useful_recall']>=rb['useful_recall']+.05
    gates['b2_harmful_not_worse']=lb['harmful_selection_rate']<=rb['harmful_selection_rate']
    gates['b2_strict_not_worse']=lb['strict_success']>=rb['strict_success']

    gates['hard_f_strict_ge_095']=hf['crc_r1']['strict_accuracy']>=.95
    gates['hard_f_representation_lt_fixed']=hf['crc_r1']['representation_failure_rate']<hf['fixed_basis']['representation_failure_rate']
    gates['hard_f2_strict_ge_095']=hf2['crc_r1']['strict_accuracy']>=.95
    gates['hard_f2_representation_lt_fixed']=hf2['crc_r1']['representation_failure_rate']<hf2['fixed_basis']['representation_failure_rate']
    gates['hard_f2_all_strata_ge_095']=all(x['strict_accuracy']>=.95 for x in hf2['crc_r1']['by_stratum'].values())

    mg=meta['result']
    gates['meta_g_strict_ge_090']=mg['strict_integrated_accuracy']>=.90
    gates['meta_g_execution_ge_095']=mg['execution_accuracy']>=.95
    gates['meta_g_planning_ge_095']=mg['planning_accuracy']>=.95
    gates['meta_g_memory_ge_095']=mg['memory_retrieval_success']>=.95
    gates['meta_g_trace_complete']=mg['trace_completeness']>=.999999

    gates['memory_provenance_positive']=m8['memory']['delta_provenance']>0
    gates['future_gain_nonnegative']=m8['future']['delta_accuracy']>=0
    gates['credit_causal_gt_spurious']=m8['credit']['causal_minus_spurious_trust']>0
    gates['meta_compute_monotonic']=m8['meta']['depth_delta']>=0 and m8['meta']['expert_delta']>=0

    gates['causal_accuracy_ge_095']=causal['full']['accuracy']>=.95
    gates['causal_false_positive_zero']=causal['full']['false_causal_rate']==0
    gates['causal_beats_observation_only']=causal['full']['accuracy']>=causal['observation_only']['accuracy']+.25

    gates['info_gain_selects_diagnostic']=info.get('selected')=='diagnostic'
    gates['program_synthesis_selects_candidate']=program.get('selected') is not None and float(program.get('top_score',-1e9))>0

    payload={
      'schema':'nexus.crc_r1.validation.v3',
      'commit':commit or os.getenv('GITHUB_SHA'),
      'p1_integrity':integrity,
      'gates':gates,
      'ready_for_pre_ftx1_freeze':all(gates.values()),
      'ftx1_used':False,
      'hard_oos_d_reused_as_clean_oos':False,
      'sources':{
        'b2':'b2/one_shot_result.json',
        'hard_oos_f':'hard_oos_f/one_shot_result.json',
        'hard_oos_f2':'hard_oos_f2/one_shot_result.json',
        'meta_g':'meta_g/one_shot_result.json',
        'm8':'m8_ablation.json',
        'causal':'causal_m15.json',
        'info_gain':'info_gain_m16.json',
        'program':'program_m25.json',
        'integrity':'p1_integrity.sha256.json',
      },
    }
    data=json.dumps(payload,indent=2,sort_keys=True).encode()
    payload['manifest_sha256']=hashlib.sha256(data).hexdigest()
    return payload

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True)
    a=ap.parse_args();p=build(a.root);Path(a.out).write_text(json.dumps(p,indent=2,sort_keys=True));print(json.dumps(p,indent=2,sort_keys=True))
if __name__=='__main__':main()
