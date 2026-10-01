from __future__ import annotations
from dataclasses import dataclass
import hashlib,random
@dataclass(frozen=True)
class MemoryOp:kind:str;key:str;value:str='';evidence:str=''
@dataclass(frozen=True)
class MemoryCase:case_id:str;ops:tuple[MemoryOp,...];query_key:str;gold_value:str;gold_min_raw:int
DISTRACTOR_KEYS=tuple(f'd{i}' for i in range(100))
def generate(seed=2026093011,n=500,distractors=64):
    rng=random.Random(seed);out=[]
    for i in range(n):
        key=f'target_{i}';v1=f'v{rng.randrange(1000)}';v2=f'v{rng.randrange(1000,2000)}';ops=[MemoryOp('UPSERT',key,v1,f'raw:first:{i}')]
        for j in range(distractors):ops.append(MemoryOp('UPSERT',rng.choice(DISTRACTOR_KEYS),f'x{rng.randrange(9999)}',f'distractor:{i}:{j}'))
        ops.append(MemoryOp('UPSERT',key,v2,f'raw:revision:{i}'))
        for j in range(distractors):ops.append(MemoryOp('UPSERT',rng.choice(DISTRACTOR_KEYS),f'y{rng.randrange(9999)}',f'late:{i}:{j}'))
        cid=hashlib.sha256(f'MEM:{seed}:{i}'.encode()).hexdigest()[:24];out.append(MemoryCase(cid,tuple(ops),key,v2,2))
    return tuple(out)
