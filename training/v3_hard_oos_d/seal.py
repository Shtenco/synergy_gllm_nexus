from __future__ import annotations
from pathlib import Path
import hashlib,json
from .generator import HardOOSDGenerator
from .programs import topology_inventory
EXPECTED_MODEL_SHA='95fd54d5036c7dfda0da1b9edbff5b804e6fa7163aab2fec83459075eb3b2c96'
def sha256_file(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def verify_checkpoint_hash(path,expected=EXPECTED_MODEL_SHA):
    got=sha256_file(path)
    if got!=expected: raise ValueError(f'checkpoint hash mismatch: {got}')
    return got
def canonical_corpus_hash(rows):
    h=hashlib.sha256()
    for r in rows:
        h.update(json.dumps(r.scorer_record(),sort_keys=True,separators=(',',':')).encode()); h.update(b'\n')
    return h.hexdigest()
def seal(output_dir,checkpoint,seed=404):
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); model_sha=verify_checkpoint_hash(checkpoint)
    rows=HardOOSDGenerator(seed).generate(); corpus_sha=canonical_corpus_hash(rows)
    inv=sorted(topology_inventory())
    summary={'episodes':len(rows),'counts':{s:sum(r.stratum==s for r in rows) for s in sorted({r.stratum for r in rows})}}
    (out/'corpus_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True),encoding='utf-8')
    (out/'topology_inventory.json').write_text(json.dumps(inv,indent=2),encoding='utf-8')
    manifest={'generator_version':'hard-oos-d-v1','seed':seed,'episode_count':len(rows),'corpus_sha256':corpus_sha,'model_sha256':model_sha,'sealed_before_evaluation':True,'consumed':False}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding='utf-8')
    return manifest
