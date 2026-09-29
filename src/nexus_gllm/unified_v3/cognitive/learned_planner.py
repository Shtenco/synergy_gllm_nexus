from __future__ import annotations
from dataclasses import dataclass
from .future_tree import BranchValue,FutureBranch,FutureTreePlanner
from .world_model import EmpiricalWorldModel
@dataclass(frozen=True)
class PlannedAction:
    action:str|None;value:float;branch_id:str|None;depth:int
class LearnedFuturePlanner:
    def __init__(self,world_model:EmpiricalWorldModel,*,max_depth=3,fanout=4,beam_width=12,gamma=.95):
        self.model=world_model;self.max_depth=max_depth;self.fanout=fanout;self.beam_width=beam_width;self.gamma=gamma
    def _expand(self,branch):
        acts=self.model.known_actions(branch.state)
        for a in acts[:self.fanout]:
            p=self.model.predict(branch.state,a)
            yield a,p.next_state,a
    def _evaluate(self,state,action,depth):
        p=self.model.predict(state,action)
        return BranchValue(expected_reward=(self.gamma**max(0,depth-1))*p.expected_reward,uncertainty=p.uncertainty,compute_cost=.01*depth)
    def plan(self,state):
        tree=FutureTreePlanner(max_depth=self.max_depth,fanout=self.fanout,beam_width=self.beam_width,weights=(1,0,0,.25,.1,0))
        nodes=tree.plan(state,self._expand,self._evaluate)
        if len(nodes)<=1:return PlannedAction(None,0.0,None,0)
        # Accumulate discounted reward along each branch ancestry instead of selecting only terminal local reward.
        by={n.branch_id:n for n in nodes};scored=[]
        for n in nodes[1:]:
            cur=n;score=0.0;depth=0
            while cur.parent_id is not None:
                pred=self.model.predict(by[cur.parent_id].state,cur.action);score+=(self.gamma**depth)*(pred.expected_reward-.25*pred.uncertainty);depth+=1;cur=by[cur.parent_id]
            first=n.branch_id.split('/')[1];scored.append((score,-n.depth,n.branch_id,first))
        score,negdepth,bid,first=max(scored,key=lambda x:(x[0],x[1],x[2]))
        return PlannedAction(first,score,bid,-negdepth)
