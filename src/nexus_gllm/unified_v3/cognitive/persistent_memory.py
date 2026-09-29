from __future__ import annotations
from dataclasses import dataclass
from .memory import HierarchicalMemoryStore,MemoryLevel,MemoryRecord

@dataclass(frozen=True)
class MemoryVersion:
    key:str;value:str;version:int;semantic_memory_id:str;raw_memory_id:str;supersedes:str|None=None;active:bool=True

class PersistentMemoryIndex:
    """Versioned semantic memory whose every value remains traceable to RAW evidence."""
    def __init__(self,store=None):
        self.store=store or HierarchicalMemoryStore();self._versions:dict[str,list[MemoryVersion]]={}
    def upsert(self,key,value,*,evidence,tags=(),confidence=1.0):
        raw=self.store.add_raw({'key':key,'value':value,'evidence':evidence},confidence=confidence,tags=tuple(tags)+('raw',key))
        hist=self._versions.setdefault(key,[]);prev=hist[-1] if hist else None;version=len(hist)+1
        parents=(raw.memory_id,) if prev is None else (raw.memory_id,prev.semantic_memory_id)
        sem=self.store.consolidate(MemoryLevel.SEMANTIC,{'key':key,'value':value,'version':version},parents,confidence=confidence,tags=tuple(tags)+('semantic',key))
        if prev is not None:hist[-1]=MemoryVersion(prev.key,prev.value,prev.version,prev.semantic_memory_id,prev.raw_memory_id,prev.supersedes,False)
        cur=MemoryVersion(key,value,version,sem.memory_id,raw.memory_id,prev.semantic_memory_id if prev else None,True);hist.append(cur);return cur
    def current(self,key):return self._versions.get(key,())[-1] if self._versions.get(key) else None
    def history(self,key):return tuple(self._versions.get(key,()))
    def evidence(self,key):
        cur=self.current(key)
        if cur is None:return ()
        return tuple(r for r in self.store.lineage(cur.semantic_memory_id) if r.level is MemoryLevel.RAW)
    def audit(self):return self.store.audit_provenance()
