from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib

class NodeKind(str, Enum):
    ATOM='ATOM'; AND='AND'; NOT='NOT'; IMPLIES='IMPLIES'; COMPOSE='COMPOSE'; INVERSE='INVERSE'; SYMMETRIC='SYMMETRIC'; TEMPORAL_BEFORE='TEMPORAL_BEFORE'; TEMPORAL_AFTER='TEMPORAL_AFTER'; STATE_GATE='STATE_GATE'; INHIBITOR='INHIBITOR'; EXCEPTION='EXCEPTION'; COUNTERFACTUAL_INTERVENTION='COUNTERFACTUAL_INTERVENTION'

@dataclass(frozen=True)
class AstNode:
    kind: NodeKind
    children: tuple['AstNode', ...]=()
    token: str=''
    arity: int=0
    @classmethod
    def atom(cls, token:str, arity:int=2): return cls(NodeKind.ATOM,(),token,arity)

def _shape(n:AstNode): return (n.kind.value,n.arity,tuple(_shape(c) for c in n.children))
def topology_fingerprint(node:AstNode)->str: return hashlib.sha256(repr(_shape(node)).encode()).hexdigest()
