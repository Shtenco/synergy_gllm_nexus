from __future__ import annotations
from dataclasses import dataclass
from .query_graph import build_query_graph
from .search_federation import SearchFederation
from .source_normalizer import normalize_source
from .claim_extractor import ClaimExtractor
from .evidence_graph import EvidenceGraph
from .trust_governor import TrustGovernor
from .citation_ledger import CitationLedger

@dataclass(frozen=True)
class ResearchResult:
    mode:str
    sources:int
    claims:int
    trusted:int
    evidence_graph:EvidenceGraph
    citations:CitationLedger

class ResearchReflex:
    def __init__(self,adapters,claim_extractor=None,trust_governor=None,source_fetcher=None):
        self.federation=SearchFederation(adapters)
        self.extractor=claim_extractor or ClaimExtractor()
        self.governor=trust_governor or TrustGovernor()
        self.source_fetcher=source_fetcher
    def run(self,text,graph_context=None,policy=None):
        qg=build_query_graph(text,graph_context or {},policy or {})
        g=EvidenceGraph(); ledger=CitationLedger(); trusted=0
        hits=[]
        for q in qg.queries:
            hits.extend(self.federation.search(q))
        seen=set()
        for h in hits:
            if h.url in seen: continue
            seen.add(h.url)
            content=self.source_fetcher.fetch(h) if self.source_fetcher is not None else h.snippet
            s=normalize_source(h,content,reliability=.8 if h.source_type in ('primary','official','paper','repo') else .55)
            g.add_source(s)
            for c in self.extractor.extract(s):
                g.add_claim(c); g.add_support(c.claim_id,s.source_id); ledger.add(c.claim_id,s.source_id,c.support_span)
        for cid in g.claims:
            d=self.governor.score_claim(cid,g,{})
            if d.status=='TRUSTED': trusted+=1
        return ResearchResult(qg.mode,len(g.sources),len(g.claims),trusted,g,ledger)