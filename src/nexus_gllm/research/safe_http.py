from __future__ import annotations
import socket, xml.etree.ElementTree as ET
from urllib.parse import urljoin
import httpx
from .security import validate_public_http_url

_ALLOWED=('application/json','application/atom+xml','application/xml','text/xml','text/plain','text/html')

def system_resolver(host:str):
    return sorted({x[4][0] for x in socket.getaddrinfo(host,None,type=socket.SOCK_STREAM)})

class SafeHTTPTransport:
    def __init__(self,client=None,resolver=system_resolver,max_bytes:int=2_000_000,max_redirects:int=5,timeout:float=15.0):
        self.client=client or httpx.Client(follow_redirects=False,timeout=timeout,headers={'User-Agent':'NEXUS-Research-Cortex/0.1'})
        self.resolver=resolver; self.max_bytes=max_bytes; self.max_redirects=max_redirects
    def __call__(self,method,url,*,params=None,headers=None):
        current=url
        for hop in range(self.max_redirects+1):
            validate_public_http_url(current,self.resolver)
            r=self.client.request(method,current,params=params if hop==0 else None,headers=headers)
            if r.status_code in (301,302,303,307,308):
                loc=r.headers.get('location')
                if not loc: raise ValueError('redirect without location')
                current=urljoin(current,loc); continue
            if not (200 <= r.status_code < 300): raise ValueError(f'HTTP {r.status_code}')
            raw=r.content
            if len(raw)>self.max_bytes: raise ValueError('response too large')
            ctype=r.headers.get('content-type','').split(';',1)[0].strip().lower()
            if ctype not in _ALLOWED: raise ValueError('disallowed content type')
            if ctype=='application/json': return r.json()
            text=raw.decode('utf-8','replace')
            if 'xml' in ctype or 'atom' in ctype:
                return self._xml(text)
            return {'text':text,'url':current,'content_type':ctype}
        raise ValueError('too many redirects')
    @staticmethod
    def _xml(text:str):
        root=ET.fromstring(text)
        ns={'a':'http://www.w3.org/2005/Atom'}
        entries=[]
        for e in root.findall('.//a:entry',ns):
            link=e.find('a:id',ns)
            entries.append({'url': link.text.strip() if link is not None and link.text else '', 'title': (e.findtext('a:title',default='',namespaces=ns) or '').strip(), 'summary': (e.findtext('a:summary',default='',namespaces=ns) or '').strip(), 'published': (e.findtext('a:published',default='',namespaces=ns) or '').strip()})
        return {'entries':entries}