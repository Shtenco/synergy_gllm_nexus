from __future__ import annotations
from dataclasses import dataclass
import hashlib
import importlib
import sys
from pathlib import Path

from .donor_adapters import ArtifactUnavailable

EXPECTED_BLOBS={
    'types.py':'6e483f6670633767fce8282bf3c39d470fbeba8e',
    'query_graph.py':'0186615928a4c07ff836fc9fd397513fd2585a91',
    'evidence_graph.py':'a489c4a5229a1d36478d798c980011a5ebe92e16',
    'trust_governor.py':'263f2d6f0a0e671bf9c99dfc8ce420c3c4e7d1b9',
    'scheduler.py':'98ee20a20b62079039e05105e0f9b8eafdf0eb21',
    'citation_ledger.py':'727d8a85332615f8647e53f92b58a6fb95516621',
}

def _git_blob_sha(path: Path)->str:
    b=path.read_bytes(); return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()

@dataclass(frozen=True)
class ResearchSource:
    source_id: str
    source_type: str
    reliability: float
    independence_group: str
    content_hash: str
    text: str

@dataclass(frozen=True)
class ResearchAssessment:
    status: str
    score: float
    support: float
    contradiction: float
    citations: tuple[str,...]

class Omega16ResearchAdapter:
    organ_id='research_cortex'
    source_version='Omega-1.6'
    source_commit='2b6d78d9b955bb892356a6cade50634911f7b13c'
    has_mutation_authority=False

    def __init__(self, donor_root: Path):
        donor_root=Path(donor_root); pkg=donor_root/'nexus_gllm'/'research'
        for name,expected in EXPECTED_BLOBS.items():
            p=pkg/name
            if not p.is_file(): raise ArtifactUnavailable(f'missing Ω-1.6 donor source {p}')
            actual=_git_blob_sha(p)
            if actual!=expected: raise ArtifactUnavailable(f'Ω-1.6 donor blob mismatch {name}: {actual} != {expected}')
        root=str(donor_root/'nexus_gllm')
        if root not in sys.path: sys.path.insert(0,root)
        try:
            self.types=importlib.import_module('research.types')
            self.evidence_mod=importlib.import_module('research.evidence_graph')
            self.trust_mod=importlib.import_module('research.trust_governor')
            self.ledger_mod=importlib.import_module('research.citation_ledger')
            self.query_mod=importlib.import_module('research.query_graph')
        except Exception as exc: raise ArtifactUnavailable(f'cannot import Ω-1.6 research donor: {exc}') from exc
        self.blob_identity=dict(EXPECTED_BLOBS)

    def build_query(self,text: str, *, sealed: bool=False, no_web: bool=False):
        return self.query_mod.build_query_graph(text,policy={'sealed':sealed,'no_web':no_web})

    def assess(self, claim_id: str, sources: list[ResearchSource], *, support_ids: tuple[str,...], contradiction_ids: tuple[str,...]) -> ResearchAssessment:
        graph=self.evidence_mod.EvidenceGraph(); ledger=self.ledger_mod.CitationLedger()
        for s in sources:
            rec=self.types.SourceRecord(s.source_id,f'local://{s.source_id}',s.source_id,s.content_hash,s.source_type,s.reliability,s.independence_group,content=s.text)
            graph.add_source(rec)
        for sid in support_ids:
            graph.add_support(claim_id,sid); ledger.add(claim_id,sid,graph.sources[sid].content or sid)
        for sid in contradiction_ids: graph.add_contradiction(claim_id,sid)
        decision=self.trust_mod.TrustGovernor().score_claim(claim_id,graph,{})
        citations=tuple(src for src,_ in ledger.sources_for(claim_id))
        return ResearchAssessment(decision.status,float(decision.score),float(decision.support),float(decision.contradiction),citations)
