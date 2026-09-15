from nexus_gllm.research.claim_extractor import ClaimExtractor
from nexus_gllm.research.types import SourceRecord

def test_simple_graph_claim_extraction():
    s=SourceRecord('s','https://a','A','h','primary',.9,'a',content='Автомобиль принадлежит Борису.')
    claims=ClaimExtractor().extract(s)
    assert claims and claims[0].source_id=='s' and claims[0].support_span