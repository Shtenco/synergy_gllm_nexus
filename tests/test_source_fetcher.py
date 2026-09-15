from nexus_gllm.research.fetcher import SourceFetcher
from nexus_gllm.research.types import SearchHit

class T:
    def __call__(self,method,url,params=None,headers=None):
        return {'text':'Полный текст источника','url':url,'content_type':'text/html'}

def test_fetcher_prefers_full_text_and_bounds_length():
    f=SourceFetcher(T(),max_chars=100)
    h=SearchHit('x','https://example.org/a','A','snippet',1)
    assert f.fetch(h)=='Полный текст источника'

class Bad:
    def __call__(self,*a,**k): raise RuntimeError('down')

def test_fetcher_falls_back_to_snippet():
    f=SourceFetcher(Bad())
    h=SearchHit('x','https://example.org/a','A','snippet',1)
    assert f.fetch(h)=='snippet'