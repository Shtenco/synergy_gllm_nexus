from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict,Counter
@dataclass(frozen=True)
class TransitionPrediction:
    next_state:str;expected_reward:float;uncertainty:float;count:int
class EmpiricalWorldModel:
    def __init__(self):
        self._next=defaultdict(Counter);self._reward_sum=defaultdict(float);self._reward_n=defaultdict(int)
    def observe(self,state,action,next_state,reward):
        k=(state,action);self._next[k][next_state]+=1;self._reward_sum[k]+=float(reward);self._reward_n[k]+=1
    def predict(self,state,action):
        k=(state,action);n=self._reward_n[k]
        if n<=0:return TransitionPrediction(state,0.0,1.0,0)
        nxt,c=self._next[k].most_common(1)[0];p=c/sum(self._next[k].values());r=self._reward_sum[k]/n
        return TransitionPrediction(nxt,r,1.0-p,n)
    def known_actions(self,state):
        return tuple(sorted({a for s,a in self._reward_n if s==state and self._reward_n[(s,a)]>0}))
