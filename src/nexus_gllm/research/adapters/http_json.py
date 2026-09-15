from __future__ import annotations
from .base import SearchAdapter
from ..types import SearchHit

class SearXNGAdapter(SearchAdapter):
    name='searxng'
    def __init__(self,base_url,transport): self.base_url=base_url.rstrip('/'); self.transport=transport
    def search(self,q):
        d=self.transport('GET',self.base_url+'/search',params={'q':q.text,'format':'json'})
        return [SearchHit(self.name,x.get('url',''),x.get('title',''),x.get('content',''),float(x.get('score') or 0)) for x in d.get('results',[]) if x.get('url')]

class GitHubSearchAdapter(SearchAdapter):
    name='github'
    def __init__(self,transport,token=None): self.transport=transport; self.token=token
    def search(self,q):
        headers={'Accept':'application/vnd.github+json'}
        if self.token: headers['Authorization']='Bearer '+self.token
        d=self.transport('GET','https://api.github.com/search/repositories',params={'q':q.text,'per_page':q.top_k},headers=headers)
        return [SearchHit(self.name,x.get('html_url',''),x.get('full_name',''),x.get('description') or '',float(x.get('score') or 0),source_type='repo') for x in d.get('items',[])]

class SemanticScholarAdapter(SearchAdapter):
    name='semantic_scholar'
    def __init__(self,transport): self.transport=transport
    def search(self,q):
        d=self.transport('GET','https://api.semanticscholar.org/graph/v1/paper/search',params={'query':q.text,'limit':q.top_k,'fields':'title,url,abstract,year'})
        return [SearchHit(self.name,x.get('url') or ('https://www.semanticscholar.org/paper/'+x.get('paperId','')),x.get('title',''),x.get('abstract') or '',1.0,source_type='paper',published_at=str(x.get('year') or '')) for x in d.get('data',[])]

class PubMedAdapter(SearchAdapter):
    name='pubmed'
    def __init__(self,transport): self.transport=transport
    def search(self,q):
        d=self.transport('GET','https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',params={'db':'pubmed','term':q.text,'retmode':'json','retmax':q.top_k})
        ids=d.get('esearchresult',{}).get('idlist',[])
        return [SearchHit(self.name,'https://pubmed.ncbi.nlm.nih.gov/'+str(i)+'/',f'PubMed {i}','',1.0,source_type='paper') for i in ids]

class ArxivAdapter(SearchAdapter):
    name='arxiv'
    def __init__(self,transport): self.transport=transport
    def search(self,q):
        # transport may normalize Atom XML into {'entries': [...]} for deterministic adapters/tests
        d=self.transport('GET','https://export.arxiv.org/api/query',params={'search_query':'all:'+q.text,'max_results':q.top_k})
        return [SearchHit(self.name,x.get('url',''),x.get('title',''),x.get('summary',''),1.0,source_type='paper',published_at=x.get('published')) for x in d.get('entries',[]) if x.get('url')]