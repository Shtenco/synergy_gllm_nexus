from nexus_gllm.research.adapters.http_json import SearXNGAdapter,GitHubSearchAdapter,SemanticScholarAdapter,PubMedAdapter,ArxivAdapter
from nexus_gllm.research.types import SearchQuery

def t(method,url,params=None,headers=None):
    if 'search/repositories' in url:return {'items':[{'html_url':'https://github.com/o/r','full_name':'o/r','description':'d','score':2}]}
    if 'semanticscholar' in url:return {'data':[{'paperId':'p','title':'T','abstract':'A','year':2026,'url':'https://s/p'}]}
    if 'esearch' in url:return {'esearchresult':{'idlist':['123']}}
    if 'arxiv' in url:return {'entries':[{'url':'https://arxiv.org/abs/1','title':'A','summary':'S','published':'2026'}]}
    if 'searx' in url:return {'results':[{'url':'https://x','title':'X','content':'c','score':1}]}
    return {}

def test_first_wave_adapters():
    q=SearchQuery('x')
    assert SearXNGAdapter('https://searx.test',t).search(q)[0].title=='X'
    assert GitHubSearchAdapter(t).search(q)[0].source_type=='repo'
    assert SemanticScholarAdapter(t).search(q)[0].source_type=='paper'
    assert PubMedAdapter(t).search(q)[0].url.endswith('/123/')
    assert ArxivAdapter(t).search(q)[0].url.startswith('https://arxiv')