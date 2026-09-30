from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .exact_artifacts import ArtifactCatalog,ArtifactStatus

HISTORICAL_REQUIRED=('r7l','r72','r76','r78','r710','r714','r718','r7443','omega15r2','v10','unified_r13')
HISTORICAL_ACCEPTED={ArtifactStatus.EXACT_RUNNABLE,ArtifactStatus.EXACT_DEPLOYED_RUNTIME}
OPERATIONAL_FIXED=('r7l','r72','r76','r78','r710','r714','r718','r7443','omega15r2','v10')
OPERATIONAL_AUTHORITY_CANDIDATES=('unified_r13','r13x_v3')
OPERATIONAL_ACCEPTED=HISTORICAL_ACCEPTED|{ArtifactStatus.VERIFIED_OPERATIONAL_RUNTIME}

@dataclass(frozen=True)
class FederationReadiness:
    mode:str
    ready:bool
    count:int
    required:int
    slots:tuple[tuple[str,str,str],...]
    blockers:tuple[str,...]

def historical_readiness(root:Path)->FederationReadiness:
    c=ArtifactCatalog.default(root);rows=[];block=[]
    for eid in HISTORICAL_REQUIRED:
        r=c.verify(eid);rows.append((eid,eid,r.status.value))
        if r.status not in HISTORICAL_ACCEPTED:block.append(eid)
    return FederationReadiness('historical_byte_identical',not block,len(HISTORICAL_REQUIRED)-len(block),len(HISTORICAL_REQUIRED),tuple(rows),tuple(block))

def operational_readiness(root:Path)->FederationReadiness:
    c=ArtifactCatalog.default(root);rows=[];block=[]
    for eid in OPERATIONAL_FIXED:
        r=c.verify(eid);rows.append((eid,eid,r.status.value))
        if r.status not in OPERATIONAL_ACCEPTED:block.append(eid)
    authority=None
    for eid in OPERATIONAL_AUTHORITY_CANDIDATES:
        r=c.verify(eid)
        if r.status in OPERATIONAL_ACCEPTED:
            authority=(eid,r);break
    if authority is None:
        block.append('authority_slot')
        rows.append(('authority_slot','NONE','UNAVAILABLE'))
    else:
        eid,r=authority;rows.append(('authority_slot',eid,r.status.value))
    count=11-len(block)
    return FederationReadiness('operational_verified',not block,count,11,tuple(rows),tuple(block))
