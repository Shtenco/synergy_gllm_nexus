from pathlib import Path
import json
from .generator import generate
from .runner import decide,observe
from .scorer import score
from .seal import seal,verify
def run(outdir,*,seed=2026093017,n_per_stratum=100,source_sha256='UNSET'):
    out=Path(outdir);b=generate(seed,n_per_stratum);seal(out,b,source_sha256)
    if not verify(out):raise RuntimeError('META-OOS G seal failed before decisions')
    decisions=[];preds=[]
    # Decision phase has runtime cases only. Scorer-only gold is not consulted.
    for c in b.runtime:
        loop,d,p=decide(c);decisions.append((c.case_id,loop,d));preds.append(p)
    (out/'predictions.json').write_text(json.dumps([p.__dict__ for p in preds],sort_keys=True))
    if not verify(out):raise RuntimeError('META-OOS G mutated during decision phase')
    result=score(b.runtime,b.gold,tuple(preds))
    # Observation/learning occurs only after decisions are frozen.
    gm={g.case_id:g for g in b.gold};learning=[]
    for cid,loop,d in decisions:
        o=observe(loop,d,gm[cid]);learning.append({'case_id':cid,'rpe':o.rpe,'credit_nodes':len(o.credit)})
    payload={'benchmark':'NEXUS-CRC-META-OOS-G','protocol':{'sealed_before_decision':True,'test_open_count':1,'tuning_after_open':False,'reward_after_decision_only':True,'ftx1_used':False,'hard_oos_d_reused':False},'result':result,'post_decision_learning':learning}
    (out/'one_shot_result.json').write_text(json.dumps(payload,indent=2,sort_keys=True));return payload
