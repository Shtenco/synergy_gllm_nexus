from __future__ import annotations
from .contracts import TraceEvent, ExecutionTrace

class OrganBus:
    def __init__(self): self._events=[]
    def record_call(self,organ_id:str,detail:str='ok'):
        self._events.append(TraceEvent('call',organ_id,detail))
    def record_bypass(self,organ_id:str,detail:str):
        self._events.append(TraceEvent('bypass',organ_id,detail))
    def record_commit(self,organ_id:str,detail:str):
        self._events.append(TraceEvent('commit',organ_id,detail))
    def record_reject(self,organ_id:str,detail:str):
        self._events.append(TraceEvent('reject',organ_id,detail))
    def trace(self): return ExecutionTrace(tuple(self._events))
