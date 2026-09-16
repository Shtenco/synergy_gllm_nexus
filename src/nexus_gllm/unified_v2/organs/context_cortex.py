from __future__ import annotations
from collections import defaultdict

class ContextCortexV2:
    def __init__(self):
        self._facts=defaultdict(list)
        self._pending={}
    def remember(self,key,value,*,topic='default',revision=False):
        bucket=self._facts[(topic,key)]
        bucket.append(value)
        return value
    def recall(self,key,*,topic='default'):
        bucket=self._facts.get((topic,key),())
        return bucket[-1] if bucket else None
    def history(self,key,*,topic='default'):
        return tuple(self._facts.get((topic,key),()))
    def suspend_goal(self,goal_id,payload,*,topic='default'):
        self._pending[(topic,goal_id)]=dict(payload)
    def resume_goal(self,goal_id,*,topic='default'):
        x=self._pending.get((topic,goal_id))
        return dict(x) if x is not None else None
