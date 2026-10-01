from __future__ import annotations
from dataclasses import dataclass,replace
import math
from .credit import CognitiveTraceGraph
from .self_model import NexusSelfModel

@dataclass(frozen=True)
class CreditStat:
    node_id:str;kind:str;count:int=0;mean_credit:float=0.0;positive_mass:float=0.0;negative_mass:float=0.0
    @property
    def trust(self):
        return 1.0/(1.0+math.exp(-2.0*self.mean_credit))

class RecursiveCreditLearner:
    """Turn RPE/trace credit into persistent component reliability statistics.

    Counterfactual / leave-one-out credit can be supplied per node. When
    available it is blended with graph-propagated credit so correlated
    contributors do not all receive identical outcome credit.
    """
    def __init__(self,self_model=None,blend=.5):
        self.stats={}
        self.self_model=self_model or NexusSelfModel()
        self.blend=float(blend)
    def update(self,graph:CognitiveTraceGraph,outcome_node_id:str,rpe:float,*,counterfactual_credit=None,decay=.9):
        propagated=graph.propagate(outcome_node_id,rpe,decay=decay)
        cf=counterfactual_credit or {}
        merged={}
        for node_id,node in graph.nodes.items():
            if node_id==outcome_node_id:continue
            p=float(propagated.get(node_id,0.0));c=float(cf.get(node_id,p));credit=(1-self.blend)*p+self.blend*c
            old=self.stats.get(node_id,CreditStat(node_id,node.kind));n=old.count+1;mean=old.mean_credit+(credit-old.mean_credit)/n
            stat=CreditStat(node_id,node.kind,n,mean,old.positive_mass+max(0,credit),old.negative_mass+max(0,-credit));self.stats[node_id]=stat;merged[node_id]=credit
            payload=node.payload if isinstance(node.payload,dict) else {}
            cap=payload.get('capability') or f'{node.kind}:{node_id}'
            self.self_model.observe(cap,success=credit>=0,credit=credit)
        return merged
    def get(self,node_id):return self.stats.get(node_id)
    def trust(self,node_id,default=.5):
        s=self.get(node_id);return default if s is None else s.trust
    def ranked(self,kind=None):
        xs=[s for s in self.stats.values() if kind is None or s.kind==kind]
        return tuple(sorted(xs,key=lambda s:(-s.trust,-s.count,s.node_id)))
