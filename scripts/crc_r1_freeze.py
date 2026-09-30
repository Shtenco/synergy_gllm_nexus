from __future__ import annotations
import argparse,json,os
from pathlib import Path
from nexus_gllm.unified_v3.cognitive.pre_ftx1 import PreFTX1FreezeGate

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--evidence',default='artifacts/crc_r1_validation/PRE_FTX1_EVIDENCE_MANIFEST.json')
    ap.add_argument('--out',default='artifacts/crc_r1_validation/CRC_R1_PRE_FTX1_FREEZE.json')
    ap.add_argument('--commit',default=os.getenv('GITHUB_SHA'))
    a=ap.parse_args()
    if not a.commit: raise SystemExit('commit is required')
    payload=PreFTX1FreezeGate().freeze(a.evidence,a.out,commit=a.commit)
    print(json.dumps(payload,indent=2,sort_keys=True))
if __name__=='__main__':main()
