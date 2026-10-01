from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,random
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind,ProgramNode

STRATA=('if_false','inhibit_open','cf_flip_false','cf_remove_unknown','nested_negative_gate','mixed_negative_cf')

def n(kind,symbol='',children=(),params=()): return ProgramNode(kind,symbol,tuple(children),tuple(params))
def atom(rule,op,q): return n(ProgramKind.ATOM,f'rule:{rule}:{op}',params=(('query_operator',q[0]),('query_src',q[1]),('query_dst',q[2])))
def topo(x): return (x.kind.value,tuple(topo(c) for c in x.children))
def th(x): return hashlib.sha256(repr(topo(x)).encode()).hexdigest()

@dataclass(frozen=True)
class RuntimeCase:
    case_id:str;stratum:str;ast:dict;world:tuple[tuple[str,str,str,bool],...];task:tuple[str,str,str]
@dataclass(frozen=True)
class Gold:
    case_id:str;expected_status:str;expected_truth:bool|None;topology_sha256:str
@dataclass(frozen=True)
class Bundle:
    runtime:tuple[RuntimeCase,...];gold:tuple[Gold,...]

def cid(seed,i): return hashlib.sha256(f'HARD-OOS-F2:{seed}:{i}'.encode()).hexdigest()[:24]

def make(rng,seed,i,stratum):
    nonce=f'n{rng.randrange(10**7,10**8)}';r=f'r_{nonce}';g=f'g_{nonce}';b=f'b_{nonce}';q=(r,'a','c')
    body=atom('transitive',r,q)
    gq=(g,'x','y');bq=(b,'u','v')
    guard=atom('transitive',g,gq);block=atom('transitive',b,bq)
    world=[(r,'a','b',True),(r,'b','c',True)]
    if stratum=='if_false':
        world.append((g,'x','y',False));ast=n(ProgramKind.IF,children=(guard,body));status,truth='CONDITION_FALSE',False
    elif stratum=='inhibit_open':
        world.append((b,'u','v',False));ast=n(ProgramKind.INHIBIT,children=(block,body));status,truth='EXECUTED',True
    elif stratum=='cf_flip_false':
        world=[(r,'a','c',True)];ast=n(ProgramKind.COUNTERFACTUAL,children=(body,),params=(('kind','FLIP_POLARITY'),('operator',r),('src','a'),('dst','c')));status,truth='EXECUTED',False
    elif stratum=='cf_remove_unknown':
        world=[(r,'a','c',True)];ast=n(ProgramKind.COUNTERFACTUAL,children=(body,),params=(('kind','REMOVE_FACT'),('operator',r),('src','a'),('dst','c')));status,truth='EXECUTED',None
    elif stratum=='nested_negative_gate':
        world.append((g,'x','y',False));world.append((b,'u','v',False));inner=n(ProgramKind.INHIBIT,children=(block,body));ast=n(ProgramKind.IF,children=(guard,inner));status,truth='CONDITION_FALSE',False
    else:
        world=[(g,'x','y',True),(r,'a','c',True)]
        cf=n(ProgramKind.COUNTERFACTUAL,children=(body,),params=(('kind','FLIP_POLARITY'),('operator',r),('src','a'),('dst','c')))
        ast=n(ProgramKind.IF,children=(guard,cf));status,truth='EXECUTED',False
    c=cid(seed,i);return RuntimeCase(c,stratum,ast.canonical(),tuple(world),q),Gold(c,status,truth,th(ast))

def generate(seed=2026093031,n_per_stratum=200):
    rng=random.Random(seed);rs=[];gs=[];i=0
    for s in STRATA:
        for _ in range(n_per_stratum):
            r,g=make(rng,seed,i,s);rs.append(r);gs.append(g);i+=1
    order=list(range(len(rs)));rng.shuffle(order);return Bundle(tuple(rs[j] for j in order),tuple(gs[j] for j in order))

def runtime_jsonl(b): return '\n'.join(json.dumps(x.__dict__,sort_keys=True,separators=(',',':')) for x in b.runtime)+'\n'
def gold_jsonl(b):
    gm={g.case_id:g for g in b.gold}
    return '\n'.join(json.dumps(gm[x.case_id].__dict__,sort_keys=True,separators=(',',':')) for x in b.runtime)+'\n'
