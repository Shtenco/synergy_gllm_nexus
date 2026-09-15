from nexus_gllm.research.evidence_graph import EvidenceGraph
from nexus_gllm.research.types import SourceRecord, ClaimProposal

def test_dependency_and_contradiction_edges():
    g=EvidenceGraph()
    s1=SourceRecord('s1','https://a','A','h1','primary',0.9,'wire1')
    s2=SourceRecord('s2','https://b','B','h2','secondary',0.7,'wire1')
    g.add_source(s1); g.add_source(s2)
    c=ClaimProposal('c','X','is_a','Y','X is Y','span','s1',0.9)
    g.add_claim(c); g.add_support('c','s1'); g.add_support('c','s2'); g.add_contradiction('c','s2')
    assert g.dependency('s1','s2')==1.0
    assert 's2' in g.contradicts['c']