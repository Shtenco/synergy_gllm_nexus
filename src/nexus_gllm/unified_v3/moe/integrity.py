from pathlib import Path
import hashlib,json
import torch
from .learned_router import P1_PAYLOAD_FILES,P1_INTEGRITY_FILE

P1_TORCH_FILES=('router.pt','novelty.pt','calibrator.pt')
P1_RECOVERY_FILE='recovery.json'

def _sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def logical_state_hash(state):
    """Canonical P1 logical checkpoint hash; byte-for-byte identical to training.v3_moe.train_router.logical_state_hash."""
    h=hashlib.sha256()
    for k,v in sorted(state.items()):
        h.update(k.encode());h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()

def validate_torch_payloads(artifact_dir):
    root=Path(artifact_dir);logical={};loadability={}
    for name in P1_TORCH_FILES:
        try:
            state=torch.load(root/name,map_location='cpu',weights_only=True)
            if not isinstance(state,dict):raise TypeError('checkpoint state must be a dict')
            logical[name]=logical_state_hash(state);loadability[name]=True
        except Exception as exc:
            raise RuntimeError(f'{name} is not a loadable frozen checkpoint: {type(exc).__name__}: {exc}') from exc
    recovery=root/P1_RECOVERY_FILE
    if recovery.is_file():
        expected=json.loads(recovery.read_text(encoding='utf-8')).get('logical_state_sha256',{})
        bad=[name for name in P1_TORCH_FILES if name in expected and logical.get(name)!=expected[name]]
        if bad:raise RuntimeError('logical state hash mismatch: '+','.join(bad))
    return {'loadability':loadability,'logical_state_sha256':logical}

def generate_integrity_manifest(artifact_dir,*,source_commit=None):
    root=Path(artifact_dir);sha={}
    for name in P1_PAYLOAD_FILES:
        sha[name]=_sha(root/name)
    verified=validate_torch_payloads(root)
    payload={'format_version':2,'source_commit':source_commit,'sha256':sha,**verified}
    if (root/P1_RECOVERY_FILE).is_file():payload['recovery_sha256']=_sha(root/P1_RECOVERY_FILE)
    (root/P1_INTEGRITY_FILE).write_text(json.dumps(payload,indent=2,sort_keys=True),encoding='utf-8')
    return payload
