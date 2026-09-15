from __future__ import annotations
from typing import Protocol, Any
from ..types import SearchQuery, SearchHit

class JSONTransport(Protocol):
    def __call__(self, method:str, url:str, *, params:dict|None=None, headers:dict|None=None) -> Any: ...

class SearchAdapter:
    name='base'; networked=True
    def search(self,query:SearchQuery)->list[SearchHit]: raise NotImplementedError