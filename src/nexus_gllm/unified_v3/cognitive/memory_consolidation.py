from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
import json
from .memory import HierarchicalMemoryStore,MemoryLevel,MemoryRecord

@dataclass(frozen=True)
class ConsolidationProposal:
    target_level:MemoryLevel
    parent_ids:tuple[str,...]
    payload:dict
    confidence:float
    reason:str

@dataclass(frozen=True)
class ConsolidationResult:
    created:tuple[MemoryRecord,...]
    skipped:tuple[str,...]
    raw_provenance_before:tuple[str,...]
    raw_provenance_after:tuple[str,...]

class EvidencePreservingConsolidator:
    """Promote repeated evidence upward without deleting or merging contradictions."""
    def __init__(self,store:HierarchicalMemoryStore,min_support=2,min_confidence=.70):
        self.store=store;self.min_support=int(min_support);self.min_confidence=float(min_confidence)

    @staticmethod
    def _payload_key(rec:MemoryRecord):
        p=rec.payload
        if isinstance(p,dict):
            if 'key' in p and 'value' in p:return ('kv',str(p['key']),json.dumps(p['value'],sort_keys=True,ensure_ascii=False,default=repr))
            if 'fact' in p:return ('fact',json.dumps(p['fact'],sort_keys=True,ensure_ascii=False,default=repr))
        return ('raw',json.dumps(p,sort_keys=True,ensure_ascii=False,default=repr))

    def propose_semantic(self,records):
        groups=defaultdict(list)
        for r in records:
            if r.level not in (MemoryLevel.RAW,MemoryLevel.EPISODIC):continue
            groups[self._payload_key(r)].append(r)
        out=[]
        by_subject=defaultdict(set)
        for key,rows in groups.items():
            if key[0]=='kv':by_subject[key[1]].add(key[2])
        conflicts={k for k,v in by_subject.items() if len(v)>1}
        for key,rows in sorted(groups.items(),key=lambda x:repr(x[0])):
            if len(rows)<self.min_support:continue
            if key[0]=='kv' and key[1] in conflicts:continue
            conf=sum(r.confidence for r in rows)/len(rows)
            if conf<self.min_confidence:continue
            payload={'consolidated_key':key,'support_count':len(rows)}
            out.append(ConsolidationProposal(MemoryLevel.SEMANTIC,tuple(r.memory_id for r in rows),payload,conf,'repeated_consistent_evidence'))
        return tuple(out)

    def apply(self,proposals):
        before=tuple(sorted(r.memory_id for r in self.store._records.values() if r.level is MemoryLevel.RAW))
        created=[];skipped=[]
        for p in proposals:
            try:
                rec=self.store.consolidate(p.target_level,p.payload,p.parent_ids,confidence=p.confidence,tags=('auto_consolidated',))
                created.append(rec)
            except Exception as exc:
                skipped.append(f'{p.reason}:{type(exc).__name__}')
        after_raw=tuple(sorted({raw for rec in created for raw in rec.raw_provenance}))
        return ConsolidationResult(tuple(created),tuple(skipped),before,after_raw)

    def working_set(self,query_tags=(),limit=16):
        rows=self.store.retrieve(query_tags,limit=limit)
        # Prefer higher abstractions, but raw records remain retrievable through lineage.
        return tuple(sorted(rows,key=lambda r:(-list(MemoryLevel).index(r.level),-r.confidence,r.memory_id)))
