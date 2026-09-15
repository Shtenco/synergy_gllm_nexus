from __future__ import annotations
import json
from .types import SearchHit

class SourceFetcher:
    def __init__(self,transport,max_chars:int=200_000):
        self.transport=transport; self.max_chars=max_chars
    def fetch(self,hit:SearchHit)->str:
        try:
            data=self.transport('GET',hit.url,headers={'Accept':'text/html,text/plain,application/json,application/xml,text/xml'})
            if isinstance(data,dict) and isinstance(data.get('text'),str): text=data['text']
            elif isinstance(data,(dict,list)): text=json.dumps(data,ensure_ascii=False)
            elif isinstance(data,str): text=data
            else: text=''
            text=text.strip()
            if text: return text[:self.max_chars]
        except Exception:
            pass
        return (hit.snippet or '')[:self.max_chars]