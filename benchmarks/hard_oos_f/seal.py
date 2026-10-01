from pathlib import Path
import hashlib,json
from .generator import runtime_jsonl,gold_jsonl
def seal(outdir,bundle,source_sha256):
    o=Path(outdir);o.mkdir(parents=True,exist_ok=True);rb=runtime_jsonl(bundle).encode();gb=gold_jsonl(bundle).encode();(o/'runtime.jsonl').write_bytes(rb);(o/'scorer_only_gold.jsonl').write_bytes(gb);m={'benchmark':'NEXUS-HARD-OOS-F','version':1,'runtime_sha256':hashlib.sha256(rb).hexdigest(),'gold_sha256':hashlib.sha256(gb).hexdigest(),'source_sha256':source_sha256,'cases':len(bundle.runtime),'sealed_before_evaluation':True,'hard_oos_d_used_for_tuning':False,'ftx1_used':False,'test_open_count':0};(o/'freeze_manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True));return m
def verify(outdir):
    o=Path(outdir);m=json.loads((o/'freeze_manifest.json').read_text());return hashlib.sha256((o/'runtime.jsonl').read_bytes()).hexdigest()==m['runtime_sha256'] and hashlib.sha256((o/'scorer_only_gold.jsonl').read_bytes()).hexdigest()==m['gold_sha256']
