import pytest
from nexus_gllm.research.safe_http import SafeHTTPTransport

class R:
    def __init__(self,status=200,headers=None,content=b'{}'):
        self.status_code=status; self.headers=headers or {'content-type':'application/json'}; self.content=content
    def json(self):
        import json; return json.loads(self.content)

class C:
    def __init__(self,responses): self.responses=list(responses); self.calls=[]
    def request(self,method,url,params=None,headers=None):
        self.calls.append(url); return self.responses.pop(0)

def public(host): return ['93.184.216.34']
def private(host): return ['127.0.0.1']

def test_transport_validates_redirect_hops_and_parses_json():
    c=C([R(302,{'location':'https://b.example/x','content-type':'text/plain'},b''),R(200,{'content-type':'application/json'},b'{"x":1}')])
    t=SafeHTTPTransport(client=c,resolver=public)
    assert t('GET','https://a.example/q')=={'x':1}
    assert c.calls==['https://a.example/q','https://b.example/x']

def test_transport_blocks_private_dns_before_request():
    c=C([]); t=SafeHTTPTransport(client=c,resolver=private)
    with pytest.raises(ValueError): t('GET','https://internal.example/q')
    assert c.calls==[]

def test_transport_rejects_oversized_or_bad_type():
    c=C([R(200,{'content-type':'application/octet-stream'},b'abc')]); t=SafeHTTPTransport(client=c,resolver=public)
    with pytest.raises(ValueError): t('GET','https://a.example/q')