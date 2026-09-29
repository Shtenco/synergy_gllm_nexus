from __future__ import annotations
from pathlib import Path
import hashlib,json,os
def _load(p):return json.loads(Path(p).read_text())
def build(root,*,commit=None):
    root=Path(root);b2=_load(root/'b2'/'one_shot_result.json');hf=_load(root/'hard_oos_f'/'one_shot_result.json');m8=_load(root/'m8_ablation.json');integrity=_load(root/'p1_integrity.sha256.json')
    gates={}
    lb=b2['learned_or_candidate']['overall'];rb=b2['random']['overall']
    gates['b2_beats_random_recall']=lb['useful_recall']>=rb['useful_recall']+.05
    gates['b2_harmful_not_worse']=lb['harmful_selection_rate']<=rb['harmful_selection_rate']
    gates['b2_strict_not_worse']=lb['strict_success']>=rb['strict_success']
    gates['hard_f_strict_ge_095']=hf['crc_r1']['strict_accuracy']>=.95
    gates['hard_f_representation_lt_fixed']=hf['crc_r1']['representation_failure_rate']<hf['fixed_basis']['representation_failure_rate']
    gates['memory_provenance_positive']=m8['memory']['delta_provenance']>0
    gates['future_gain_nonnegative']=m8['future']['delta_accuracy']>=0
    gates['credit_causal_gt_spurious']=m8['credit']['causal_minus_spurious_trust']>0
    gates['meta_compute_monotonic']=m8['meta']['depth_delta']>=0 and m8['meta']['expert_delta']>=0
    payload={'schema':'nexus.crc_r1.validation.v1','commit':commit or os.getenv('GITHUB_SHA'),'p1_integrity':integrity,'gates':gates,'ready_for_pre_ftx1_freeze':all(gates.values()),'ftx1_used':False,'hard_oos_d_reused_as_clean_oos':False,'sources':{'b2':'b2/one_shot_result.json','hard_oos_f':'hard_oos_f/one_shot_result.json','m8':'m8_ablation.json','integrity':'p1_integrity.sha256.json'}}
    data=json.dumps(payload,indent=2,sort_keys=True).encode();payload['manifest_sha256']=hashlib.sha256(data).hexdigest();return payload
def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();p=build(a.root);Path(a.out).write_text(json.dumps(p,indent=2,sort_keys=True));print(json.dumps(p,indent=2,sort_keys=True))
if __name__=='__main__':main()
