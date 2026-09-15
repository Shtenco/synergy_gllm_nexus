from __future__ import annotations
import hashlib
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
from .types import SearchHit,SourceRecord
_TRACK_PREFIX=('utm_','fbclid','gclid','mc_')

def normalize_url(url:str)->str:
    p=urlsplit(url)
    q=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if not any(k.lower().startswith(x) for x in _TRACK_PREFIX)]
    host=(p.hostname or '').lower()
    netloc=host + ((f':{p.port}') if p.port and not ((p.scheme=='https' and p.port==443) or (p.scheme=='http' and p.port==80)) else '')
    path=p.path or '/'
    return urlunsplit((p.scheme.lower(),netloc,path,urlencode(q),''))

def normalize_source(hit:SearchHit,content:str='',redirects=(),reliability:float=.5)->SourceRecord:
    url=normalize_url(hit.url)
    h=hashlib.sha256(content.encode('utf-8')).hexdigest()
    sid=hashlib.sha256((url+'\0'+h).encode()).hexdigest()[:24]
    group=hit.metadata.get('independence_group') if hit.metadata else None
    group=group or (urlsplit(url).hostname or url)
    return SourceRecord(sid,url,hit.title,h,hit.source_type,reliability,str(group),hit.published_at,None,content)