from __future__ import annotations
from collections import defaultdict
from .types import SourceRecord,ClaimProposal

class EvidenceGraph:
    def __init__(self):
        self.sources={}; self.claims={}; self.supports=defaultdict(set); self.contradicts=defaultdict(set)
    def add_source(self,s:SourceRecord): self.sources[s.source_id]=s
    def add_claim(self,c:ClaimProposal): self.claims[c.claim_id]=c
    def add_support(self,claim_id,source_id): self.supports[claim_id].add(source_id)
    def add_contradiction(self,claim_id,source_id): self.contradicts[claim_id].add(source_id)
    def dependency(self,a,b)->float:
        if a==b:return 1.0
        sa,sb=self.sources[a],self.sources[b]
        if sa.independence_group==sb.independence_group:return 1.0
        if sa.content_hash and sa.content_hash==sb.content_hash:return 1.0
        return 0.0