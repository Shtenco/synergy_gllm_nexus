from __future__ import annotations
from dataclasses import fields,is_dataclass
import hashlib
from .contracts import Entity,OperatorSymbol,SemanticAtom,SemanticObservation

FORBIDDEN={'prompt','text','text_ru','raw_text','history','document','documents','renderer'+'_id','split'+'_id','track'+'_id'}

def _canon(v):
    if isinstance(v,Entity): return ('E',v.entity_id.casefold())
    if isinstance(v,OperatorSymbol): return ('O',v.operator_id.casefold(),v.arity)
    if isinstance(v,SemanticAtom): return ('A',_canon(v.operator),tuple(_canon(x) for x in v.arguments),v.polarity)
    if isinstance(v,SemanticObservation): return ('OBS',tuple(_canon(x) for x in v.atoms))
    if isinstance(v,(tuple,list)): return tuple(_canon(x) for x in v)
    return v

def semantic_fingerprint(observation:SemanticObservation)->str:
    return hashlib.sha256(repr(_canon(observation)).encode()).hexdigest()

def assert_text_quarantined(value:object)->None:
    seen=set()
    def walk(x):
        oid=id(x)
        if oid in seen: return
        seen.add(oid)
        if is_dataclass(x):
            for f in fields(x):
                if f.name in FORBIDDEN:
                    raise ValueError(f'raw text field forbidden in reasoning contract: {f.name}')
                walk(getattr(x,f.name))
        elif isinstance(x,dict):
            for k,v in x.items():
                if str(k) in FORBIDDEN: raise ValueError(f'raw text field forbidden in reasoning contract: {k}')
                walk(v)
        elif isinstance(x,(tuple,list,set,frozenset)):
            for y in x: walk(y)
    walk(value)
