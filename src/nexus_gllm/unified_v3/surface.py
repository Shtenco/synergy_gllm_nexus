from __future__ import annotations
from dataclasses import dataclass
import re
from .contracts import Entity,OperatorSymbol,SemanticAtom,SemanticObservation

@dataclass(frozen=True)
class SurfaceRequest:
    text: str=''
    structured_operator: str|None=None
    structured_edges: tuple[tuple[str,str],...]=()
    structured_query: tuple[str,str]|None=None
    @classmethod
    def structured_relation(cls,operator_id,edges,query):
        return cls('',operator_id,tuple(edges),tuple(query))

def _entity_id(token:str)->str:
    t=token.casefold()
    if t.endswith(('ой','ей')) and len(t)>3: return t[:-2]+'а'
    if t.endswith(('ы','и')) and len(t)>3: return t[:-1]+'а'
    if t.endswith(('у','ю')) and len(t)>3: return t[:-1]
    return t

class ControlledSurfaceAdapter:
    def parse(self,request:SurfaceRequest)->SemanticObservation:
        if request.structured_operator:
            op=OperatorSymbol(request.structured_operator,2)
            return SemanticObservation(tuple(SemanticAtom(op,(Entity(_entity_id(a)),Entity(_entity_id(b)))) for a,b in request.structured_edges))
        s=request.text.strip().rstrip('.')
        patterns=[
            (r'^(\w+) передала? (\w+) (\w+)$',lambda m:(m.group(1),m.group(2),m.group(3))),
            (r'^(\w+) был передан (\w+) (\w+)$',lambda m:(m.group(3),m.group(1),m.group(2))),
            (r'^(\w+) получил от (\w+) (\w+)$',lambda m:(m.group(2),m.group(3),m.group(1))),
        ]
        for pat,fn in patterns:
            m=re.match(pat,s,re.I|re.U)
            if m:
                src,obj,dst=fn(m)
                op=OperatorSymbol('op:transfer',3)
                return SemanticObservation((SemanticAtom(op,(Entity(_entity_id(src)),Entity(_entity_id(obj)),Entity(_entity_id(dst)))),))
        raise ValueError('unsupported controlled surface')
