from __future__ import annotations
from .types import ResearchNeed

class ResearchScheduler:
    def __init__(self,max_queries:int=8,epsilon:float=.05):
        self.max_queries=max_queries; self.epsilon=epsilon; self.seen=set(); self.used=0
    @staticmethod
    def utility(n:ResearchNeed)->float:
        return n.expected_gain*n.importance*n.novelty/max(1e-9,n.cost+n.latency+n.risk)
    def choose(self,needs:list[ResearchNeed]):
        if self.used>=self.max_queries:return None
        cand=[n for n in needs if n.query not in self.seen]
        if not cand:return None
        best=max(cand,key=self.utility)
        return best if self.utility(best)>=self.epsilon else None
    def record(self,query:str):
        self.seen.add(query); self.used+=1