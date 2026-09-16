from __future__ import annotations
import argparse, json
from pathlib import Path
from benchmarks.ub2.run_dev_shadow import run
from nexus_gllm.unified_v2.preblind_runtime import UnifiedNexusV2Preblind


def run_ablations(seed: int, workspace_root: Path):
    baseline=run(seed,workspace_root)
    ablations={}
    for organ in UnifiedNexusV2Preblind.ORGAN_IDS:
        r=run(seed,workspace_root,disabled_organs={organ})
        r['delta_full_vs_baseline']=r['full_score']-baseline['full_score']
        ablations[organ]=r
    return {
        'seed':seed,
        'baseline':baseline,
        'ablations':ablations,
        'interpretation':'A zero delta means the current UB2 synthetic predictor does not measure this organ independently; it does not prove the organ is useless.',
    }

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,required=True);ap.add_argument('--workspace-root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    r=run_ablations(a.seed,a.workspace_root);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'baseline':r['baseline']['full_score'],'deltas':{k:v['delta_full_vs_baseline'] for k,v in r['ablations'].items()}},ensure_ascii=False,indent=2))
