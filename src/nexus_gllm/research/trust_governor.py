from __future__ import annotations
import math
from .types import ClaimDecision

class TrustGovernor:
    def __init__(self,dependency_lambda:float=.6): self.dependency_lambda=dependency_lambda
    def _weight(self,s,ctx):
        direct=1.0 if s.source_type in ('primary','official','paper','repo') else .75
        freshness=ctx.get('freshness_factor',1.0)
        return max(0.0,min(1.0,s.reliability))*direct*freshness
    def score_claim(self,claim_id,graph,query_context)->ClaimDecision:
        sup=list(graph.supports.get(claim_id,()))
        con=list(graph.contradicts.get(claim_id,()))
        sw=[self._weight(graph.sources[s],query_context) for s in sup]
        cw=[self._weight(graph.sources[s],query_context) for s in con]
        penalty=0.0
        for ids,ws in ((sup,sw),(con,cw)):
            for i in range(len(ids)):
                for j in range(i+1,len(ids)):
                    penalty+=self.dependency_lambda*graph.dependency(ids[i],ids[j])*min(ws[i],ws[j])
        logit=sum(sw)-sum(cw)-penalty
        score=1/(1+math.exp(-logit))
        status='TRUSTED' if score>=.8 and sum(sw)>sum(cw) else ('CONFLICTED' if cw and sw else ('CANDIDATE' if score>=.55 else 'REJECTED'))
        return ClaimDecision(status,score,sum(sw),sum(cw))