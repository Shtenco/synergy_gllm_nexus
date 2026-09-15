from __future__ import annotations
import re
from dataclasses import dataclass
from .types import SearchQuery

@dataclass(frozen=True)
class QueryGraph:
    original: str
    mode: str
    freshness: bool
    deep_intent: bool
    queries: tuple[SearchQuery,...]

def build_query_graph(text:str, graph_context:dict|None=None, policy:dict|None=None)->QueryGraph:
    policy=policy or {}; low=text.lower().strip()
    if policy.get('sealed'): return QueryGraph(text,'SEALED',False,False,())
    if policy.get('no_web'): return QueryGraph(text,'OFFLINE',False,False,())
    if re.fullmatch(r'[\d\s+\-*/().=]+', low): return QueryGraph(text,'OFFLINE',False,False,())
    freshness=any(k in low for k in ('сегодня','сейчас','последн','latest','current','новост','цена','курс'))
    deep=any(k in low for k in ('исслед','аудит','сравни','найди все','deep research','подробно')) or freshness
    mode='DEEP' if deep else 'PROBE'
    qs=[SearchQuery(text,mode=mode,top_k=12 if deep else 8)]
    if deep:
        qs.append(SearchQuery(text+' первоисточник',mode=mode,top_k=8))
    return QueryGraph(text,mode,freshness,deep,tuple(qs))