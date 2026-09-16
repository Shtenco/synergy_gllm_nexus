from __future__ import annotations
from dataclasses import dataclass
import hashlib
import importlib.util
import sys
from pathlib import Path

from .donor_adapters import ArtifactUnavailable

EXPECTED_CRITIC='75a72c2b43693f1a84921722f632162edecb903441ecb26eedd7176c47a0a81e'
EXPECTED_RUNTIME='00e5c3866bf8f19e61eff922998afce057a6bd572a2f749527fbd6830dd57691'


def _sha(p: Path): return hashlib.sha256(p.read_bytes()).hexdigest()

@dataclass(frozen=True)
class RecurrentAdvice:
    answer: str|None
    stage: str|None
    risk: float
    suggested_teacher: str|None
    feedback_digest: str
    commit_authority: bool=False


class R717RecurrentReasonerAdapter:
    organ_id='recurrent_reasoner'
    source_version='R7.17'
    has_commit_authority=False

    def __init__(self, root: Path):
        root=Path(root); runtime=root/'source'/'runtime_r717.py'; critic=root/'models'/'recurrent_critic.pt'
        if not runtime.is_file() or not critic.is_file(): raise ArtifactUnavailable(f'missing R7.17 artifacts under {root}')
        self.runtime_sha256=_sha(runtime); self.critic_sha256=_sha(critic)
        if self.runtime_sha256!=EXPECTED_RUNTIME or self.critic_sha256!=EXPECTED_CRITIC:
            raise ArtifactUnavailable('R7.17 digest mismatch')
        src=str(root/'source')
        if src not in sys.path: sys.path.insert(0,src)
        name='nexus_v2_r717_'+self.runtime_sha256[:12]
        spec=importlib.util.spec_from_file_location(name,runtime)
        if spec is None or spec.loader is None: raise ArtifactUnavailable('cannot load R7.17 runtime')
        mod=importlib.util.module_from_spec(spec)
        try: spec.loader.exec_module(mod)
        except Exception as exc: raise ArtifactUnavailable(f'cannot load R7.17 runtime: {exc}') from exc
        self.module=mod

    def advise_mcq(self,item: dict, teacher_rows: dict|None=None) -> RecurrentAdvice:
        out=self.module.decide(item,teacher_rows or {})
        fb=out.get('recurrent_feedback') or {}
        ans=out.get('answer'); ans=ans if ans in {'A','B','C','D'} else None
        return RecurrentAdvice(ans,out.get('stage'),float(fb.get('risk_current_hypothesis',1.0)),fb.get('suggested_teacher_one_step'),str(fb.get('feedback_digest','')),False)
