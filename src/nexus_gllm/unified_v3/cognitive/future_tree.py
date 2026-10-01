from __future__ import annotations
from dataclasses import dataclass,field
from typing import Any,Callable,Iterable
@dataclass(frozen=True)
class BranchValue:
    expected_reward:float=0.0;information_gain:float=0.0;causal_consistency:float=0.0;uncertainty:float=0.0;compute_cost:float=0.0;risk:float=0.0
    def scalar(self,weights=(1.0,.35,.35,.45,.20,.50)):
        a,b,g,d,l,m=weights; return a*self.expected_reward+b*self.information_gain+g*self.causal_consistency-d*self.uncertainty-l*self.compute_cost-m*self.risk
@dataclass(frozen=True)
class FutureBranch:
    branch_id:str;state:Any;action:Any=None;depth:int=0;value:BranchValue=field(default_factory=BranchValue);parent_id:str|None=None
class FutureTreePlanner:
    def __init__(self,*,max_depth=3,fanout=4,beam_width=8,weights=(1.0,.35,.35,.45,.20,.50)): self.max_depth=max_depth;self.fanout=fanout;self.beam_width=beam_width;self.weights=weights
    def plan(self,root_state,expand,evaluate):
        root=FutureBranch("root",root_state,depth=0);beam=(root,);all_nodes=[root]
        for depth in range(1,self.max_depth+1):
            nxt=[]
            for parent in beam:
                for suffix,state,action in list(expand(parent))[:self.fanout]:
                    bid=f"{parent.branch_id}/{suffix}"; node=FutureBranch(bid,state,action,depth,evaluate(state,action,depth),parent.branch_id);nxt.append(node);all_nodes.append(node)
            if not nxt: break
            nxt.sort(key=lambda b:(-b.value.scalar(self.weights),b.branch_id));beam=tuple(nxt[:self.beam_width])
        return tuple(all_nodes)
    def best(self,branches):
        xs=[b for b in branches if b.depth>0]; return max(xs,key=lambda b:(b.value.scalar(self.weights),-b.depth,b.branch_id)) if xs else None
