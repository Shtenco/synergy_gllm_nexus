from nexus_gllm.research.evidence_graph import EvidenceGraph
from nexus_gllm.research.types import SourceRecord, ClaimProposal
from nexus_gllm.research.trust_governor import TrustGovernor

def _g(independent=True):
    g=EvidenceGraph(); c=ClaimProposal('c','X','is_a','Y','x','span','s1',0.9); g.add_claim(c)
    g.add_source(SourceRecord('s1','https://a','A','h1','primary',0.95,'a')); g.add_support('c','s1')
    g.add_source(SourceRecord('s2','https://b','B','h2','primary',0.95,'b' if independent else 'a')); g.add_support('c','s2')
    return g

def test_independent_sources_score_higher_than_syndicated():
    gov=TrustGovernor()
    assert gov.score_claim('c',_g(True),{}).score > gov.score_claim('c',_g(False),{}).score