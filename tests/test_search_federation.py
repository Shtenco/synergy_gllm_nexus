from nexus_gllm.research.types import SearchQuery, SearchHit
from nexus_gllm.research.search_federation import SearchFederation

class A:
    name='a'; networked=True
    def search(self,q): return [SearchHit('a','https://x.test/a','A','one',1.0)]
class B:
    name='b'; networked=True
    def search(self,q): return [SearchHit('b','https://x.test/a','A2','two',0.9),SearchHit('b','https://y.test/b','B','b',0.8)]

def test_merge_dedupe_and_sealed():
    f=SearchFederation([A(),B()])
    hits=f.search(SearchQuery('q',mode='PROBE'))
    assert [h.url for h in hits]==['https://x.test/a','https://y.test/b']
    assert f.search(SearchQuery('q',mode='SEALED'))==[]