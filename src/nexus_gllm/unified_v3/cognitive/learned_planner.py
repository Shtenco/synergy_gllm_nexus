from __future__ import annotations
from dataclasses import dataclass
from .world_model import EmpiricalWorldModel

@dataclass(frozen=True)
class PlannedAction:
    action:str|None
    value:float
    branch_id:str|None
    depth:int

@dataclass(frozen=True)
class _BeamNode:
    state:str
    first_action:str|None
    branch_id:str
    depth:int
    cumulative_value:float

class LearnedFuturePlanner:
    """Bounded beam planner over a learned empirical transition/reward model.

    Each edge is scored from the *parent* state/action transition. This matters:
    evaluating the child state with the same action would attribute reward to the
    wrong transition and can prune the correct long-horizon branch.
    """
    def __init__(self,world_model:EmpiricalWorldModel,*,max_depth=3,fanout=4,beam_width=12,gamma=.95,uncertainty_penalty=.25):
        self.model=world_model
        self.max_depth=max_depth
        self.fanout=fanout
        self.beam_width=beam_width
        self.gamma=gamma
        self.uncertainty_penalty=uncertainty_penalty

    def plan(self,state):
        root=_BeamNode(state,None,'root',0,0.0)
        beam=(root,)
        all_nodes=[root]
        for depth in range(1,self.max_depth+1):
            nxt=[]
            for parent in beam:
                for action in self.model.known_actions(parent.state)[:self.fanout]:
                    pred=self.model.predict(parent.state,action)
                    edge=(self.gamma**(depth-1))*(pred.expected_reward-self.uncertainty_penalty*pred.uncertainty)
                    first=parent.first_action or action
                    node=_BeamNode(pred.next_state,first,f'{parent.branch_id}/{action}',depth,parent.cumulative_value+edge)
                    nxt.append(node);all_nodes.append(node)
            if not nxt:break
            nxt.sort(key=lambda n:(-n.cumulative_value,n.depth,n.branch_id))
            beam=tuple(nxt[:self.beam_width])
        candidates=[n for n in all_nodes if n.depth>0]
        if not candidates:return PlannedAction(None,0.0,None,0)
        best=max(candidates,key=lambda n:(n.cumulative_value,-n.depth,n.branch_id))
        return PlannedAction(best.first_action,best.cumulative_value,best.branch_id,best.depth)
