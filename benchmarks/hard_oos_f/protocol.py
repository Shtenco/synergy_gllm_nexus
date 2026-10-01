from pathlib import Path
import json
from .generator import generate
from .runner import crc_predict,fixed_basis_predict
from .scorer import score
from .seal import seal,verify
def run(outdir,*,seed=2026093007,n_per_stratum=200,source_sha256='UNSET'):
    out=Path(outdir);b=generate(seed,n_per_stratum);seal(out,b,source_sha256)
    if not verify(out):raise RuntimeError('HARD-OOS F seal failed before execution')
    fixed=tuple(fixed_basis_predict(c) for c in b.runtime);crc=tuple(crc_predict(c) for c in b.runtime)
    (out/'predictions.json').write_text(json.dumps({'fixed':[p.__dict__ for p in fixed],'crc':[p.__dict__ for p in crc]},sort_keys=True))
    if not verify(out):raise RuntimeError('HARD-OOS F mutated during execution')
    result={'benchmark':'NEXUS-HARD-OOS-F','protocol':{'test_open_count':1,'tuning_after_open':False,'hard_oos_d_used_for_tuning':False,'ftx1_used':False},'fixed_basis':score(b.runtime,b.gold,fixed),'crc_r1':score(b.runtime,b.gold,crc)}
    (out/'one_shot_result.json').write_text(json.dumps(result,indent=2,sort_keys=True));return result
