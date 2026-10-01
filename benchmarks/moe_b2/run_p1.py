from __future__ import annotations
import argparse,os
from pathlib import Path
from .p1_adapter import FrozenP1B2Adapter
from .protocol import run_one_shot

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--artifact-dir',default='artifacts/v3_moe/p1');ap.add_argument('--seed',type=int,default=2026093001);ap.add_argument('--n-per-stratum',type=int,default=400);a=ap.parse_args()
    adapter=FrozenP1B2Adapter(Path(a.artifact_dir))
    validated_commit=os.getenv('NEXUS_VALIDATED_COMMIT') or os.getenv('GITHUB_SHA','LOCAL_UNVERIFIED')
    result=run_one_shot(Path(a.out),adapter.route,seed=a.seed,n_per_stratum=a.n_per_stratum,source_sha256=validated_commit)
    print(result)
if __name__=='__main__':main()
