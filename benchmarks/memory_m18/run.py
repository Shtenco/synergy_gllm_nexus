from nexus_gllm.unified_v3.cognitive.memory import HierarchicalMemoryStore,MemoryLevel
from nexus_gllm.unified_v3.cognitive.memory_consolidation import EvidencePreservingConsolidator

def build(repetitions=5):
    s=HierarchicalMemoryStore()
    for i in range(repetitions):s.add_raw({'key':'capital','value':'Astana','evidence':f'e{i}'},confidence=.95,tags=('geo',))
    return s

def run():
    s=build();c=EvidencePreservingConsolidator(s);p=c.propose_semantic(tuple(s._records.values()));r=c.apply(p)
    return {'raw_records':sum(x.level is MemoryLevel.RAW for x in s._records.values()),'semantic_created':len(r.created),'created_raw_provenance':len(r.created[0].raw_provenance) if r.created else 0,'audit_errors':s.audit_provenance()}
