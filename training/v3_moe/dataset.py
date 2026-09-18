from __future__ import annotations
from dataclasses import dataclass
import random,uuid
EXPERTS=('r7l','r72','r718','r744','graph','v3')
FEATURES=('support','ru','evidence','context','graph','novelty','proof','cost')
WEIGHTS=((2.0,.25,.10,-.15,.10,.85,.15,-.25),(.75,1.70,.10,.05,.30,.10,.10,-.20),(.10,.10,1.70,.10,.15,.30,.85,-.20),(.05,.35,.10,1.80,.10,.20,.10,-.15),(.10,.45,.20,.10,1.65,.20,.20,-.20),(.45,.10,.45,.50,.55,1.45,.75,-.30))
@dataclass(frozen=True)
class RouterEpisode:
    episode_id:str; features:dict[str,float]; useful:tuple[int,...]; harmful:tuple[int,...]; utilities:tuple[float,...]
def generate_dataset(family,n,seed):
    base={'A':1001,'B':2002,'C':3003}[family]; rng=random.Random(base+seed); rows=[]; shift={'A':0.0,'B':0.03,'C':-0.025}[family]
    for _ in range(n):
        x={k:max(0.0,min(1.0,rng.betavariate(1.4,1.4)+shift*(1 if i%2==0 else -1))) for i,k in enumerate(FEATURES)}; x['cost']=rng.random()
        u=[sum(wi*x[f] for wi,f in zip(w,FEATURES))+rng.gauss(0,.035) for w in WEIGHTS]
        order=sorted(range(len(EXPERTS)),key=lambda j:u[j],reverse=True); useful=tuple(order[:2]); harmful=tuple(order[-2:])
        rows.append(RouterEpisode(f'{family}-{uuid.UUID(int=rng.getrandbits(128)).hex}',x,useful,harmful,tuple(u)))
    return rows
