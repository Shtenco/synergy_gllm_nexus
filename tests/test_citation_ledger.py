import pytest
from nexus_gllm.research.citation_ledger import CitationLedger
from nexus_gllm.research.memory_admission import MemoryAdmission

def test_citation_and_memory_tiers():
    l=CitationLedger(); l.add('claim1','s1','span1'); assert l.sources_for('claim1')==[('s1','span1')]
    with pytest.raises(ValueError): l.require('missing')
    m=MemoryAdmission(); assert m.classify(0.4,False)=='session'; assert m.classify(0.75,False)=='cache'; assert m.classify(.95,True)=='promoted'