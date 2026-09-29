from pathlib import Path
import hashlib,json
from .generator import generate
from .seal import seal,verify
from .evaluate import score,random_routes,oracle_routes
def source_fingerprint(paths):
    h=hashlib.sha256()
    for p in sorted(map(Path,paths),key=lambda x:str(x)):h.update(str(p.name).encode());h.update(b'\0');h.update(p.read_bytes());h.update(b'\0')
    return h.hexdigest()
def run_one_shot(outdir,route_fn,*,seed=2026093001,n_per_stratum=400,source_sha256='UNSET'):
    out=Path(outdir);bundle=generate(seed,n_per_stratum);seal(out,bundle,source_sha256)
    if not verify(out):raise RuntimeError('B2 seal verification failed before opening')
    routes=tuple(route_fn(c) for c in bundle.runtime);(out/'routes.json').write_text(json.dumps([{'case_id':c.case_id,'selected':r.selected,'probabilities':r.probabilities,'abstain':r.abstain} for c,r in zip(bundle.runtime,routes)],sort_keys=True),encoding='utf-8')
    if not verify(out):raise RuntimeError('B2 seal mutated during routing')
    result={'benchmark':'NEXUS-MOE-B2','protocol':{'sealed_before_evaluation':True,'test_open_count':1,'tuning_after_open':False,'ftx1_used':False,'hard_oos_d_reused':False},'learned_or_candidate':score(bundle.runtime,bundle.gold,routes),'random':score(bundle.runtime,bundle.gold,random_routes(bundle.runtime,seed+99)),'oracle':score(bundle.runtime,bundle.gold,oracle_routes(bundle.runtime,bundle.gold))}
    (out/'one_shot_result.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8');return result
