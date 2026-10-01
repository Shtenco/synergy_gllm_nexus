from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,random
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind,ProgramNode

STRATA=('nested_if_cf','temporal_if','inhibit_cf','temporal_inhibit','deep_mixed','surface_nonce')

def _node(kind,symbol='',children=(),params=()):return ProgramNode(kind,symbol,tuple(children),tuple(params))
def _atom(rule,op,query):return _node(ProgramKind.ATOM,f'rule:{rule}:{op}',params=(('query_operator',query[0]),('query_src',query[1]),('query_dst',query[2])))
def _canon(n):return n.canonical()
def topology(n):
    return (n.kind.value,tuple(topology(c) for c in n.children))
def topo_hash(n):return hashlib.sha256(repr(topology(n)).encode()).hexdigest()
@dataclass(frozen=True)
class FRuntimeCase:
    case_id:str;stratum:str;ast:dict;world:tuple[tuple[str,str,str],...];task:tuple[str,str,str];ledger:tuple[tuple[str,str,str,int,bool],...]
@dataclass(frozen=True)
class FGold:
    case_id:str;expected_status:str;expected_truth:bool|None;topology_sha256:str;requires_higher_order:bool
@dataclass(frozen=True)
class FBundle:runtime:tuple[FRuntimeCase,...];gold:tuple[FGold,...]

def _cid(seed,i):return hashlib.sha256(f'HARD-OOS-F:{seed}:{i}'.encode()).hexdigest()[:24]
def _case(rng,seed,i,stratum):
    nonce=f'n{rng.randrange(10**7,10**8)}'; r=f'r_{nonce}'; guard=f'g_{nonce}'; block=f'b_{nonce}'
    world=((r,'a','b'),(guard,'x','y'));task=(r,'a','c');ledger=(('state','node','ready',3,False),)
    body=_atom('transitive',r,task)
    cf=_node(ProgramKind.COUNTERFACTUAL,children=(body,),params=(('kind','ADD_FACT'),('operator',r),('src','b'),('dst','c')))
    guard_atom=_atom('transitive',guard,(guard,'x','y'))
    block_atom=_atom('transitive',block,(block,'u','v'))
    temporal=_node(ProgramKind.TEMPORAL,children=(_atom('transitive','state',('state','node','ready')),),params=(('mode','current'),))
    if stratum=='nested_if_cf':
        ast=_node(ProgramKind.IF,children=(guard_atom,cf)); status,truth='EXECUTED',True
    elif stratum=='temporal_if':
        ast=_node(ProgramKind.IF,children=(temporal,cf));status,truth='EXECUTED',True
    elif stratum=='inhibit_cf':
        ast=_node(ProgramKind.INHIBIT,children=(block_atom,cf));status,truth='UNRESOLVED',None
    elif stratum=='temporal_inhibit':
        ast=_node(ProgramKind.INHIBIT,children=(temporal,cf));status,truth='INHIBITED',None
    elif stratum=='deep_mixed':
        inner=_node(ProgramKind.IF,children=(guard_atom,cf));ast=_node(ProgramKind.COMPOSE,children=(temporal,inner));status,truth='EXECUTED',True
    else:
        renamed=f'z_{rng.randrange(10**8,10**9)}';world=((renamed,'a','b'),(guard,'x','y'));task=(renamed,'a','c');body=_atom('transitive',renamed,task);cf=_node(ProgramKind.COUNTERFACTUAL,children=(body,),params=(('kind','ADD_FACT'),('operator',renamed),('src','b'),('dst','c')));ast=_node(ProgramKind.IF,children=(guard_atom,cf));status,truth='EXECUTED',True
    cid=_cid(seed,i);rt=FRuntimeCase(cid,stratum,_canon(ast),world,task,ledger);gold=FGold(cid,status,truth,topo_hash(ast),True);return rt,gold

def generate(seed=2026093007,n_per_stratum=200):
    rng=random.Random(seed);rs=[];gs=[];i=0
    for s in STRATA:
        for _ in range(n_per_stratum):
            r,g=_case(rng,seed,i,s);rs.append(r);gs.append(g);i+=1
    order=list(range(len(rs)));rng.shuffle(order);return FBundle(tuple(rs[j] for j in order),tuple(gs[j] for j in order))

def runtime_jsonl(b):return '\n'.join(json.dumps(r.__dict__,sort_keys=True,separators=(',',':')) for r in b.runtime)+'\n'
def gold_jsonl(b):
    gm={g.case_id:g for g in b.gold}
    return '\n'.join(json.dumps(gm[r.case_id].__dict__,sort_keys=True,separators=(',',':')) for r in b.runtime)+'\n'
