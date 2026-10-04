from __future__ import annotations
from dataclasses import dataclass
from typing import Any
@dataclass(frozen=True)
class CreditNode: node_id:str;kind:str;payload:Any=None
@dataclass(frozen=True)
class CreditEdge: parent_id:str;child_id:str;responsibility:float=1.0
class CognitiveTraceGraph:
    def __init__(self): self.nodes={};self.edges=[]
    def add_node(self,node_id,kind,payload=None): self.nodes[node_id]=CreditNode(node_id,kind,payload);return node_id
    def connect(self,parent_id,child_id,responsibility=1.0):
        if parent_id not in self.nodes or child_id not in self.nodes: raise KeyError("credit edge references unknown node")
        if responsibility<0: raise ValueError("responsibility must be non-negative")
        self.edges.append(CreditEdge(parent_id,child_id,float(responsibility)));return self
    def _incoming(self,child_id): return [e for e in self.edges if e.child_id==child_id]
    def _credit_eligible(self,node_id):
        node=self.nodes[node_id];payload=node.payload if isinstance(node.payload,dict) else {}
        if 'credit_eligible' in payload:return bool(payload['credit_eligible'])
        if node.kind=='program' and 'verified' in payload:return bool(payload['verified'])
        if node.kind=='memory' and 'grounded' in payload:return bool(payload['grounded'])
        if node.kind=='meta' and 'adaptive' in payload:return bool(payload['adaptive'])
        if node.kind=='causal' and 'identified' in payload:return bool(payload['identified'])
        return True
    def propagate(self,outcome_node_id,rpe,*,decay=.9,max_hops=32):
        if outcome_node_id not in self.nodes: raise KeyError(outcome_node_id)
        credit={outcome_node_id:float(rpe)};frontier=[(outcome_node_id,float(rpe),0)]
        while frontier:
            child,amount,hops=frontier.pop(0)
            if hops>=max_hops: continue
            incoming=[e for e in self._incoming(child) if self._credit_eligible(e.parent_id)]
            total=sum(e.responsibility for e in incoming)
            if total<=0: continue
            for e in incoming:
                c=amount*decay*(e.responsibility/total);credit[e.parent_id]=credit.get(e.parent_id,0.0)+c;frontier.append((e.parent_id,c,hops+1))
        return credit
    def leave_one_out_credit(self,node_ids,baseline_score,ablate): return {node_id:float(baseline_score)-float(ablate(node_id)) for node_id in node_ids}
