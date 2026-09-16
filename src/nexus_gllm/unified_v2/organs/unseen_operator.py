from __future__ import annotations
import hashlib
from pathlib import Path
import torch

from .donor_adapters import ArtifactUnavailable
from .r72_operator_adapter import _R7Core

EXPECTED={
  711:'c447d872a0e9299aa3bbf0e82ad884c9b9ba4fcdf7514960c91b33d2ee50aff3',
  712:'a6b949fde908aa801b5c69e702e1710d32e84e1c2627d0fadd9aab71e5cb7c18',
  713:'b01679fa280a375966fae3221b98abe7528d5188675bae702f1f9c122b33116f',
}


def _sha(path: Path): return hashlib.sha256(path.read_bytes()).hexdigest()


class R7LUnseenOperatorAdapter:
    organ_id='unseen_operator'
    source_version='R7-L'
    has_commit_authority=False

    def __init__(self, root: Path, *, seed: int=712):
        root=Path(root); path=root/f'r7_seed{seed}.pt'
        if not path.is_file(): raise ArtifactUnavailable(f'missing R7-L checkpoint {path}')
        self.checkpoint_sha256=_sha(path)
        if self.checkpoint_sha256 != EXPECTED[seed]:
            raise ArtifactUnavailable(f'R7-L checkpoint digest mismatch: {self.checkpoint_sha256}')
        self.seed=seed; self.model=_R7Core()
        state=torch.load(path,map_location='cpu',weights_only=True)
        self.model.load_state_dict(state); self.model.eval()

    def solve_structured(self, support: list[tuple[int,int,int]], *, query_state: int, intent: int) -> int:
        if len(support)!=3: raise ValueError('R7-L requires exactly three support demonstrations')
        if query_state not in range(4) or intent not in (0,1): raise ValueError('invalid structured query')
        s=torch.zeros(1,3,12)
        for j,(state,effect,action) in enumerate(support):
            if state not in range(4) or effect not in range(4) or action not in range(4): raise ValueError('invalid support symbol')
            s[0,j,state]=1; s[0,j,4+effect]=1; s[0,j,8+action]=1
        q=torch.zeros(1,6); q[0,query_state]=1; q[0,4+intent]=1
        with torch.no_grad():
            effect_logits,action_logits=self.model(s,q)
        logits=effect_logits if intent==0 else action_logits
        return int(logits.argmax(-1)[0])
