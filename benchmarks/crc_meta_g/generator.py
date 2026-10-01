from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,random
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind,ProgramNode

STRATA=('cf_chain','temporal_guard','inhibit_unknown','deep_integrated')

@dataclass(frozen=True)
class RuntimeCase:
    case_id:str
    stratum:str
    world:tuple[tuple[str,str,str],...]
    task:tuple[str,str,str]
    ast:dict
    ledger:tuple[tuple[str,str,str,int,bool],...]
    memory:tuple[tuple[str,str],...]
    memory_tags:tuple[str,...]
    transitions:tuple[tuple[str,str,str,float],...]
    planning_state:str
    novelty:float
    uncertainty:float
    predicted_outcome_reward:float

@dataclass(frozen=True)
class Gold:
    case_id:str
    execution_status:str
    execution_truth:bool|None
    first_action:str|None
    min_memories:int
    observed_task_reward:float

@dataclass(frozen=True)
class Bundle:
    runtime:tuple[RuntimeCase,...]
    gold:tuple[Gold,...]

def _atom(rule,op,q):
    return ProgramNode(ProgramKind.ATOM,f'rule:{rule}:{op}',params=(('query_operator',q[0]),('query_src',q[1]),('query_dst',q[2])))
def _cid(seed,i):return hashlib.sha256(f'CRC-META-G:{seed}:{i}'.encode()).hexdigest()[:24]

def _make(rng,seed,i,stratum):
    n=f'n{i}_{rng.randrange(100000,999999)}';r=f'r_{n}';guard=f'g_{n}';block=f'b_{n}'
    task=(r,'a','c');world=((r,'a','b'),(guard,'x','y'))
    body=_atom('transitive',r,task)
    cf=ProgramNode(ProgramKind.COUNTERFACTUAL,children=(body,),params=(('kind','ADD_FACT'),('operator',r),('src','b'),('dst','c')))
    ledger=(('state',n,'ready',2,False),)
    temporal=ProgramNode(ProgramKind.TEMPORAL,children=(_atom('transitive','state',('state',n,'ready')),),params=(('mode','current'),))
    guard_atom=_atom('transitive',guard,(guard,'x','y'))
    blocker=_atom('transitive',block,(block,'u','v'))
    if stratum=='cf_chain':
        ast=cf;status,truth='EXECUTED',True
    elif stratum=='temporal_guard':
        ast=ProgramNode(ProgramKind.IF,children=(temporal,cf));status,truth='EXECUTED',True
    elif stratum=='inhibit_unknown':
        ast=ProgramNode(ProgramKind.INHIBIT,children=(blocker,cf));status,truth='UNRESOLVED',None
    else:
        guarded=ProgramNode(ProgramKind.IF,children=(guard_atom,cf))
        ast=ProgramNode(ProgramKind.COMPOSE,children=(temporal,guarded));status,truth='EXECUTED',True

    safe=.55+rng.random()*.08;future=1.4+rng.random()*.4
    transitions=(('s','safe','done',safe),('s','invest','mid',-.08),('mid','continue','goal',future))
    novelty=.78+rng.random()*.18;uncertainty=.60+rng.random()*.25
    memory=((f'fact:{n}:0','raw-a'),(f'fact:{n}:1','raw-b'),(f'distractor:{i}','noise'))
    cid=_cid(seed,i)
    rt=RuntimeCase(cid,stratum,world,task,ast.canonical(),ledger,memory,('meta-g',),transitions,'s',novelty,uncertainty,.0)
    reward=1.0 if truth is True else .2
    return rt,Gold(cid,status,truth,'invest',2,reward)

def generate(seed=2026093017,n_per_stratum=100):
    rng=random.Random(seed);rs=[];gs=[];i=0
    for s in STRATA:
        for _ in range(n_per_stratum):
            r,g=_make(rng,seed,i,s);rs.append(r);gs.append(g);i+=1
    order=list(range(len(rs)));rng.shuffle(order)
    return Bundle(tuple(rs[j] for j in order),tuple(gs[j] for j in order))

def runtime_jsonl(b):
    return '\n'.join(json.dumps(r.__dict__,sort_keys=True,separators=(',',':')) for r in b.runtime)+'\n'
def gold_jsonl(b):
    gm={g.case_id:g for g in b.gold}
    return '\n'.join(json.dumps(gm[r.case_id].__dict__,sort_keys=True,separators=(',',':')) for r in b.runtime)+'\n'
