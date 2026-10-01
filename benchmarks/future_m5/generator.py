from __future__ import annotations
from dataclasses import dataclass
import random
@dataclass(frozen=True)
class Transition:state:str;action:str;next_state:str;reward:float
@dataclass(frozen=True)
class Env:transitions:tuple[Transition,...];start:str;optimal_first:str
def generate(seed=2026093013,n=200):
    rng=random.Random(seed);envs=[]
    for i in range(n):
        s=f's{i}';safe=f'safe{i}';invest=f'invest{i}';jack=f'jack{i}'
        safe_now=.55+rng.random()*.10;invest_now=-.05-rng.random()*.05;jackpot=1.5+rng.random()*.5
        rows=(Transition(s,'safe',safe,safe_now),Transition(s,'invest',invest,invest_now),Transition(safe,'finish',safe,0.0),Transition(invest,'continue',jack,jackpot),Transition(jack,'finish',jack,0.0))
        envs.append(Env(rows,s,'invest'))
    return tuple(envs)
