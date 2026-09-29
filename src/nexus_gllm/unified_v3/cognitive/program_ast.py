from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib,json
from typing import Iterable
class ProgramKind(str,Enum):
    ATOM="ATOM";SEQUENCE="SEQUENCE";COMPOSE="COMPOSE";IF="IF";INHIBIT="INHIBIT";TEMPORAL="TEMPORAL";COUNTERFACTUAL="COUNTERFACTUAL"
@dataclass(frozen=True)
class ProgramNode:
    kind:ProgramKind; symbol:str=""; children:tuple["ProgramNode",...]=(); params:tuple[tuple[str,str],...]=()
    def canonical(self): return {"kind":self.kind.value,"symbol":self.symbol,"params":list(sorted(self.params)),"children":[c.canonical() for c in self.children]}
    @property
    def program_id(self):
        b=json.dumps(self.canonical(),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode(); return "prog:"+hashlib.sha256(b).hexdigest()[:24]
    @property
    def depth(self): return 1+max((c.depth for c in self.children),default=0)
    @property
    def complexity(self): return 1+sum(c.complexity for c in self.children)
class ProgramSynthesizer:
    def atoms(self,symbols): return tuple(ProgramNode(ProgramKind.ATOM,s) for s in dict.fromkeys(symbols))
    def expand(self,base,*,max_depth=4,max_candidates=128):
        pool={n.program_id:n for n in base}; frontier=list(pool.values()); unary=(ProgramKind.TEMPORAL,ProgramKind.COUNTERFACTUAL); binary=(ProgramKind.SEQUENCE,ProgramKind.COMPOSE,ProgramKind.IF,ProgramKind.INHIBIT)
        while frontier and len(pool)<max_candidates:
            current=frontier.pop(0)
            for kind in unary:
                n=ProgramNode(kind,children=(current,))
                if n.depth<=max_depth and n.program_id not in pool: pool[n.program_id]=n;frontier.append(n)
                if len(pool)>=max_candidates: break
            if len(pool)>=max_candidates: break
            for other in list(pool.values())[:32]:
                for kind in binary:
                    n=ProgramNode(kind,children=(current,other))
                    if n.depth<=max_depth and n.program_id not in pool: pool[n.program_id]=n;frontier.append(n)
                    if len(pool)>=max_candidates: break
                if len(pool)>=max_candidates: break
        return tuple(sorted(pool.values(),key=lambda n:(n.complexity,n.program_id)))
