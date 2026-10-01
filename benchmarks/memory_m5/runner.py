from dataclasses import dataclass
from nexus_gllm.unified_v3.cognitive.persistent_memory import PersistentMemoryIndex
@dataclass(frozen=True)
class MemoryPrediction:case_id:str;value:str|None;raw_evidence_count:int
class FlatWindowMemory:
    def __init__(self,window=32):self.window=window;self.rows=[]
    def upsert(self,key,value,evidence):self.rows.append((key,value,evidence));self.rows=self.rows[-self.window:]
    def current(self,key):
        for k,v,e in reversed(self.rows):
            if k==key:return v
        return None
def hierarchical_predict(case):
    m=PersistentMemoryIndex()
    for op in case.ops:
        if op.kind=='UPSERT':m.upsert(op.key,op.value,evidence=op.evidence,tags=('bench',))
    cur=m.current(case.query_key);return MemoryPrediction(case.case_id,cur.value if cur else None,len(m.evidence(case.query_key)))
def flat_predict(case,window=32):
    m=FlatWindowMemory(window)
    for op in case.ops:m.upsert(op.key,op.value,op.evidence)
    return MemoryPrediction(case.case_id,m.current(case.query_key),0)
