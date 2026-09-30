from pathlib import Path
import hashlib,json
from .generator import runtime_jsonl,gold_jsonl
def h(b): return hashlib.sha256(b).hexdigest()
def seal(outdir,bundle,source_sha256):
    o=Path(outdir);o.mkdir(parents=True,exist_ok=True);r=runtime_jsonl(bundle).encode();g=gold_jsonl(bundle).encode();(o/'runtime.jsonl').write_bytes(r);(o/'scorer_only_gold.jsonl').write_bytes(g);m={'benchmark':'NEXUS-HARD-OOS-F2','version':1,'runtime_sha256':h(r),'gold_sha256':h(g),'source_sha256':source_sha256,'sealed_before_evaluation':True,'ftx1_used':False,'hard_oos_d_reused':False};(o/'freeze_manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True));return m
def verify(outdir):
    o=Path(outdir);m=json.loads((o/'freeze_manifest.json').read_text());return h((o/'runtime.jsonl').read_bytes())==m['runtime_sha256'] and h((o/'scorer_only_gold.jsonl').read_bytes())==m['gold_sha256']
