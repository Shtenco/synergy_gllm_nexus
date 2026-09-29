from nexus_gllm.unified_v3.cognitive.memory import HierarchicalMemoryStore,MemoryLevel
from nexus_gllm.unified_v3.cognitive.memory_consolidation import EvidencePreservingConsolidator
def test_repeated_consistent_raw_evidence_consolidates_without_deletion():
    s=HierarchicalMemoryStore()
    raws=[s.add_raw({'key':'k','value':'v','evidence':i},confidence=.9) for i in range(3)]
    c=EvidencePreservingConsolidator(s);p=c.propose_semantic(tuple(s._records.values()));r=c.apply(p)
    assert len(r.created)==1 and set(r.created[0].raw_provenance)=={x.memory_id for x in raws}
    assert all(x.memory_id in s._records for x in raws) and s.audit_provenance()==()
def test_conflicting_values_are_not_auto_consolidated():
    s=HierarchicalMemoryStore();s.add_raw({'key':'k','value':'A'},confidence=.9);s.add_raw({'key':'k','value':'A'},confidence=.9);s.add_raw({'key':'k','value':'B'},confidence=.9);s.add_raw({'key':'k','value':'B'},confidence=.9)
    assert EvidencePreservingConsolidator(s).propose_semantic(tuple(s._records.values()))==()
def test_low_confidence_repetition_is_not_promoted():
    s=HierarchicalMemoryStore();s.add_raw({'key':'k','value':'v'},confidence=.4);s.add_raw({'key':'k','value':'v'},confidence=.4)
    assert EvidencePreservingConsolidator(s,min_confidence=.8).propose_semantic(tuple(s._records.values()))==()
def test_working_set_prefers_abstraction_but_lineage_stays_reversible():
    s=HierarchicalMemoryStore();raws=[s.add_raw({'key':'k','value':'v'},confidence=.9,tags=('x',)) for _ in range(2)];c=EvidencePreservingConsolidator(s);r=c.apply(c.propose_semantic(tuple(s._records.values())));rows=c.working_set(('x',),10)
    assert r.created and set(r.created[0].raw_provenance)=={x.memory_id for x in raws}
