from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from nexus_gllm.unified_v3.moe.exact_artifacts import ArtifactCatalog, ArtifactStatus

REQUIRED_EXPERTS=(
    'r7l','r72','r76','r78','r710','r714','r718','r7443','omega15r2','v10','unified_r13'
)
ACCEPTED={ArtifactStatus.EXACT_RUNNABLE,ArtifactStatus.EXACT_DEPLOYED_RUNTIME}

@dataclass(frozen=True)
class B2Readiness:
    ready:bool
    exact_count:int
    required_count:int
    statuses:tuple[tuple[str,str],...]
    blockers:tuple[str,...]

def readiness(artifact_root:Path)->B2Readiness:
    catalog=ArtifactCatalog.default(artifact_root)
    rows=[]
    blockers=[]
    for expert_id in REQUIRED_EXPERTS:
        rec=catalog.verify(expert_id)
        rows.append((expert_id,rec.status.value))
        if rec.status not in ACCEPTED:
            blockers.append(expert_id)
    return B2Readiness(
        ready=not blockers,
        exact_count=len(REQUIRED_EXPERTS)-len(blockers),
        required_count=len(REQUIRED_EXPERTS),
        statuses=tuple(rows),
        blockers=tuple(blockers),
    )

def require_11_of_11(artifact_root:Path)->B2Readiness:
    state=readiness(artifact_root)
    if not state.ready:
        raise RuntimeError(
            'NEXUS-MOE-B2/HARD-FAR-OOS is sealed fail-closed until 11/11 exact artifacts are available; '
            f'current={state.exact_count}/{state.required_count}; blockers={",".join(state.blockers)}'
        )
    return state
