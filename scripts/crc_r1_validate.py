from __future__ import annotations
import argparse,json,os,subprocess,sys
from pathlib import Path

STAGES=[
 ("pytest",[sys.executable,"-m","pytest","-q","tests/crc_r1","tests/crc_meta_g","tests/moe_b2","tests/hard_oos_f","tests/hard_oos_f2","tests/unified_v3_moe"]),
 ("compileall",[sys.executable,"-m","compileall","src","benchmarks"]),
 ("integrity",[sys.executable,"-c","from nexus_gllm.unified_v3.moe.integrity import generate_integrity_manifest; import os; print(generate_integrity_manifest('artifacts/v3_moe/p1', source_commit=os.getenv('GITHUB_SHA','PORTABLE')))"]),
 ("b2",[sys.executable,"-m","benchmarks.moe_b2.run_p1","--out","artifacts/crc_r1_validation/b2","--artifact-dir","artifacts/v3_moe/p1","--seed","2026093001","--n-per-stratum","400"]),
 ("hard_oos_f",[sys.executable,"-c","import os; from benchmarks.hard_oos_f.protocol import run; print(run('artifacts/crc_r1_validation/hard_oos_f',seed=2026093007,n_per_stratum=200,source_sha256=os.getenv('GITHUB_SHA','PORTABLE')))"]),
 ("hard_oos_f2",[sys.executable,"-c","import os; from benchmarks.hard_oos_f2.protocol import run; print(run('artifacts/crc_r1_validation/hard_oos_f2',seed=2026093031,n_per_stratum=200,source_sha256=os.getenv('GITHUB_SHA','PORTABLE')))"]),
 ("meta_g",[sys.executable,"-c","import os; from benchmarks.crc_meta_g.protocol import run; print(run('artifacts/crc_r1_validation/meta_g',seed=2026093017,n_per_stratum=100,source_sha256=os.getenv('GITHUB_SHA','PORTABLE')))"]),
 ("m8",[sys.executable,"-m","benchmarks.crc_m8.run","--out","artifacts/crc_r1_validation/m8_ablation.json"]),
 ("mechanistic",[sys.executable,"-c","import json; from pathlib import Path; from benchmarks.causal_m15.run import generate as cg,evaluate as ce; from benchmarks.info_gain_m16.run import run as irun; from benchmarks.program_m25.run import run as prun; root=Path('artifacts/crc_r1_validation'); cases=cg(seed=2026093021,n=300); (root/'causal_m15.json').write_text(json.dumps({'full':ce(cases,True),'observation_only':ce(cases,False)},indent=2,sort_keys=True)); (root/'info_gain_m16.json').write_text(json.dumps(irun(),indent=2,sort_keys=True)); (root/'program_m25.json').write_text(json.dumps(prun(),indent=2,sort_keys=True))"]),
 ("evidence_manifest",[sys.executable,"-m","benchmarks.crc_m8.evidence_manifest","--root","artifacts/crc_r1_validation","--out","artifacts/crc_r1_validation/PRE_FTX1_EVIDENCE_MANIFEST.json"]),
]

def run_stage(name,cmd,root):
    p=subprocess.run(cmd,text=True,capture_output=True)
    (root/f"{name}.stdout.log").write_text(p.stdout,encoding="utf-8")
    (root/f"{name}.stderr.log").write_text(p.stderr,encoding="utf-8")
    (root/f"{name}.exit").write_text(str(p.returncode))
    return p.returncode

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--continue-on-error",action="store_true")
    a=ap.parse_args();root=Path("artifacts/crc_r1_validation");root.mkdir(parents=True,exist_ok=True);codes={}
    for name,cmd in STAGES:
        code=run_stage(name,cmd,root);codes[name]=code
        if code and not a.continue_on_error:break
    (root/"PORTABLE_VALIDATION_STATUS.json").write_text(json.dumps({"commit":os.getenv("GITHUB_SHA"),"schema":"nexus.crc_r1.validation.v3","codes":codes},indent=2,sort_keys=True))
    raise SystemExit(1 if any(codes.values()) else 0)
if __name__=="__main__":main()
