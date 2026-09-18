from pathlib import Path
import hashlib,json

def _canon(cases):
    rows=[]
    for c in cases: rows.append({'case_id':c.case_id,'family':c.family,'text':c.text,'gold':c.gold,'options':c.options,'payload':c.payload})
    return json.dumps(rows,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def seal_b1(outdir,splits,artifact_manifest_sha256):
    o=Path(outdir);o.mkdir(parents=True,exist_ok=True); hashes={k:hashlib.sha256(_canon(v)).hexdigest() for k,v in splits.items()};m={'name':'NEXUS-MOE-B1','version':1,'counts':{k:len(v) for k,v in splits.items()},'split_sha256':hashes,'artifact_manifest_sha256':artifact_manifest_sha256,'sealed_before_evaluation':True};(o/'NEXUS_MOE_B1_FREEZE_MANIFEST.json').write_text(json.dumps(m,indent=2,sort_keys=True),encoding='utf-8');return m
def verify_sealed(outdir,splits):
    m=json.loads((Path(outdir)/'NEXUS_MOE_B1_FREEZE_MANIFEST.json').read_text());return all(hashlib.sha256(_canon(splits[k])).hexdigest()==v for k,v in m['split_sha256'].items())
