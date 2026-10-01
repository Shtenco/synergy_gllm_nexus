from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib,json
from typing import Any,Iterable

class MemoryLevel(str,Enum):
    RAW="RAW";EPISODIC="EPISODIC";SEMANTIC="SEMANTIC";CAUSAL="CAUSAL";ABSTRACT="ABSTRACT";META="META"

@dataclass(frozen=True)
class MemoryRecord:
    memory_id:str; level:MemoryLevel; payload:Any; parent_ids:tuple[str,...]=(); raw_provenance:tuple[str,...]=(); confidence:float=1.0; tags:tuple[str,...]=()

class HierarchicalMemoryStore:
    def __init__(self):
        self._records:dict[str,MemoryRecord]={}
        self._raw_ordinal=0
    @staticmethod
    def _id(level,payload,parents,instance=None):
        body=json.dumps({"level":level.value,"payload":payload,"parents":list(parents),"instance":instance},sort_keys=True,ensure_ascii=False,default=repr,separators=(",",":"))
        return "mem:"+hashlib.sha256(body.encode()).hexdigest()[:24]
    def add_raw(self,payload,*,confidence=1.0,tags=()):
        # RAW records are observations, not set members. Repeated identical evidence
        # must remain separately addressable so support counts and provenance are honest.
        ordinal=self._raw_ordinal;self._raw_ordinal+=1
        mid=self._id(MemoryLevel.RAW,payload,(),ordinal)
        rec=MemoryRecord(mid,MemoryLevel.RAW,payload,(),(mid,),float(confidence),tuple(tags));self._records[mid]=rec;return rec
    def consolidate(self,level,payload,parent_ids,*,confidence=1.0,tags=()):
        if level is MemoryLevel.RAW: raise ValueError("use add_raw for RAW memory")
        parents=tuple(dict.fromkeys(parent_ids))
        if not parents: raise ValueError("consolidated memory requires parents")
        missing=[p for p in parents if p not in self._records]
        if missing: raise KeyError(f"unknown parent memories: {missing}")
        raw=sorted({r for p in parents for r in self._records[p].raw_provenance})
        if not raw: raise ValueError("consolidation would lose raw provenance")
        mid=self._id(level,payload,parents);rec=MemoryRecord(mid,level,payload,parents,tuple(raw),float(confidence),tuple(tags));self._records[mid]=rec;return rec
    def get(self,memory_id): return self._records[memory_id]
    def lineage(self,memory_id):
        seen=set();out=[];stack=[memory_id]
        while stack:
            x=stack.pop()
            if x in seen: continue
            seen.add(x);rec=self._records[x];out.append(rec);stack.extend(rec.parent_ids)
        return tuple(out)
    def audit_provenance(self):
        errors=[]
        for mid,rec in self._records.items():
            if rec.level is MemoryLevel.RAW:
                if rec.raw_provenance!=(mid,): errors.append(f"{mid}:raw_provenance")
                continue
            if not rec.parent_ids: errors.append(f"{mid}:no_parents")
            for raw in rec.raw_provenance:
                if raw not in self._records or self._records[raw].level is not MemoryLevel.RAW: errors.append(f"{mid}:invalid_raw:{raw}")
        return tuple(errors)
    def retrieve(self,query_tags,*,limit=8,min_confidence=0.0):
        q=set(query_tags);ranked=[]
        for rec in self._records.values():
            if rec.confidence<min_confidence: continue
            overlap=len(q&set(rec.tags));level_bonus=list(MemoryLevel).index(rec.level)/100.0
            ranked.append((overlap+rec.confidence+level_bonus,rec.memory_id,rec))
        ranked.sort(key=lambda x:(-x[0],x[1]))
        return tuple(x[2] for x in ranked[:limit])
