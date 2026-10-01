from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class HypothesisMass:
    hypothesis_id:str
    probability:float

@dataclass(frozen=True)
class QueryOutcome:
    label:str
    probability:float
    posterior:tuple[HypothesisMass,...]

@dataclass(frozen=True)
class InformationQuery:
    query_id:str
    outcomes:tuple[QueryOutcome,...]
    cost:float=0.0
    risk:float=0.0

@dataclass(frozen=True)
class QueryScore:
    query_id:str
    prior_entropy:float
    expected_posterior_entropy:float
    information_gain:float
    utility:float
    cost:float
    risk:float

def entropy(masses):
    ps=[max(0.0,float(x.probability)) for x in masses]
    s=sum(ps)
    if s<=0:return 0.0
    out=0.0
    for p in ps:
        p/=s
        if p>0:out-=p*math.log2(p)
    return out

class ActiveInformationSelector:
    """Select observations/interventions by expected entropy reduction per cost/risk."""
    def __init__(self,*,cost_weight=.25,risk_weight=.75,min_gain=0.0):
        self.cost_weight=float(cost_weight);self.risk_weight=float(risk_weight);self.min_gain=float(min_gain)

    def score(self,prior,query:InformationQuery):
        h0=entropy(prior);total=sum(max(0.0,o.probability) for o in query.outcomes)
        if total<=0:
            return QueryScore(query.query_id,h0,h0,0.0,-self.cost_weight*query.cost-self.risk_weight*query.risk,query.cost,query.risk)
        eh=0.0
        for o in query.outcomes:
            w=max(0.0,o.probability)/total
            eh+=w*entropy(o.posterior)
        gain=max(0.0,h0-eh)
        utility=gain-self.cost_weight*max(0.0,query.cost)-self.risk_weight*max(0.0,query.risk)
        return QueryScore(query.query_id,h0,eh,gain,utility,query.cost,query.risk)

    def choose(self,prior,queries):
        scored=tuple(self.score(prior,q) for q in queries)
        viable=[s for s in scored if s.information_gain>=self.min_gain]
        if not viable:return None,scored
        best=max(viable,key=lambda s:(s.utility,s.information_gain,-s.risk,-s.cost,s.query_id))
        return best,scored
