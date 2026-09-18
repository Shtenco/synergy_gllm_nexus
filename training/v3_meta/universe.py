from __future__ import annotations
from dataclasses import dataclass
import random
FAMILIES=('TRANSITIVE','SYMMETRIC','INVERSE','BLOCKED')
_FAMILY_SEED={'A':101,'B':202,'C':303}
@dataclass(frozen=True)
class Candidate:
    family:str; explained:float; contradictions:float; heldout:float; complexity:float; symmetry_signal:float; chain_signal:float; inverse_signal:float; blocker_signal:float
@dataclass(frozen=True)
class Episode:
    operator_token:str; candidates:tuple[Candidate,...]; gold_index:int
class SyntheticUniverseGenerator:
    def __init__(self,family,seed):
        self.family=family; self.seed=seed; self.prefix={'A':'ta','B':'db','C':'oc'}[family]
    def generate(self,n):
        rng=random.Random(_FAMILY_SEED[self.family]*1000003+self.seed)
        out=[]
        for i in range(n):
            gold=rng.randrange(len(FAMILIES)); token=f'{self.prefix}_{i}_{rng.randrange(10**9)}'
            cs=[]
            for j,f in enumerate(FAMILIES):
                good=(j==gold)
                explained=max(0.0,min(1.0,rng.gauss(0.62 if good else 0.50,0.20)))
                contradictions=max(0.0,min(1.0,rng.gauss(0.28 if good else 0.47,0.20)))
                heldout=max(0.0,min(1.0,rng.gauss(0.67 if good else 0.48,0.20)))
                complexity=max(0.0,min(1.0,rng.gauss(0.45 if good else 0.52,0.20)))
                proto=[0.15,0.15,0.15,0.15]; proto[j]=0.85
                obs=[0.15,0.15,0.15,0.15]; obs[gold]=0.85
                compat=[max(0.0,min(1.0,1.0-abs(obs[k]-proto[k])+rng.gauss(0,0.22))) for k in range(4)]
                cs.append(Candidate(f,explained,contradictions,heldout,complexity,*compat))
            out.append(Episode(token,tuple(cs),gold))
        return out
