from __future__ import annotations
from collections import defaultdict

class CitationLedger:
    def __init__(self): self._m=defaultdict(list)
    def add(self,claim_id,source_id,support_span):
        if not source_id or not support_span: raise ValueError('citation requires source and support span')
        item=(source_id,support_span)
        if item not in self._m[claim_id]: self._m[claim_id].append(item)
    def sources_for(self,claim_id): return list(self._m.get(claim_id,()))
    def require(self,claim_id):
        out=self.sources_for(claim_id)
        if not out: raise ValueError(f'missing provenance for {claim_id}')
        return out