from __future__ import annotations
from .types import SearchQuery,SearchHit
from .source_normalizer import normalize_url

class SearchFederation:
    def __init__(self,adapters): self.adapters=list(adapters)
    def search(self,query:SearchQuery,budget:int|None=None)->list[SearchHit]:
        if query.mode in ('SEALED','OFFLINE'):
            allowed=[a for a in self.adapters if not getattr(a,'networked',True)]
        else: allowed=self.adapters
        merged={}
        for a in allowed:
            try: hits=a.search(query)
            except Exception: continue
            for h in hits:
                key=normalize_url(h.url)
                old=merged.get(key)
                if old is None or h.score>old.score: merged[key]=h
        out=sorted(merged.values(),key=lambda h:(-h.score,h.url))
        return out[:budget or query.top_k]