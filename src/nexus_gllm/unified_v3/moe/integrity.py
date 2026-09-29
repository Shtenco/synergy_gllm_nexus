from pathlib import Path
import hashlib,json
from .learned_router import P1_PAYLOAD_FILES,P1_INTEGRITY_FILE
def generate_integrity_manifest(artifact_dir,*,source_commit=None):
    root=Path(artifact_dir);sha={}
    for name in P1_PAYLOAD_FILES:
        h=hashlib.sha256()
        with (root/name).open('rb') as f:
            for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
        sha[name]=h.hexdigest()
    payload={'format_version':1,'source_commit':source_commit,'sha256':sha}
    (root/P1_INTEGRITY_FILE).write_text(json.dumps(payload,indent=2,sort_keys=True),encoding='utf-8');return payload
