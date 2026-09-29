from pathlib import Path
import hashlib,json
from .generator import runtime_jsonl,gold_jsonl
def _sha_bytes(b):return hashlib.sha256(b).hexdigest()
def seal(outdir,bundle,source_sha256):
    o=Path(outdir);o.mkdir(parents=True,exist_ok=True);rb=runtime_jsonl(bundle).encode();gb=gold_jsonl(bundle).encode();(o/'runtime.jsonl').write_bytes(rb);(o/'scorer_only_gold.jsonl').write_bytes(gb);m={'benchmark':'NEXUS-MOE-B2','version':1,'runtime_sha256':_sha_bytes(rb),'gold_sha256':_sha_bytes(gb),'source_sha256':source_sha256,'cases':len(bundle.runtime),'sealed_before_evaluation':True,'test_open_count':0,'ftx1_used':False,'hard_oos_d_reused':False};(o/'freeze_manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True),encoding='utf-8');return m
def verify(outdir):
    o=Path(outdir);m=json.loads((o/'freeze_manifest.json').read_text());return hashlib.sha256((o/'runtime.jsonl').read_bytes()).hexdigest()==m['runtime_sha256'] and hashlib.sha256((o/'scorer_only_gold.jsonl').read_bytes()).hexdigest()==m['gold_sha256']
