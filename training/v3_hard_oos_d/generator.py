from __future__ import annotations
from dataclasses import dataclass,asdict
import random,uuid
from .programs import program_templates
from .ast import topology_fingerprint
from .strata import ALLOCATIONS

@dataclass(frozen=True)
class DCandidate:
    name:str; explained:float; contradictions:float; heldout:float; complexity:float; symmetry_signal:float; chain_signal:float; inverse_signal:float; blocker_signal:float; topology:str
@dataclass(frozen=True)
class HardDEpisode:
    episode_id:str; stratum:str; candidates:tuple[DCandidate,...]; gold_index:int; gold_topology:str; gold_answer:str; hidden_fraction:float; distractor_fraction:float; noise_fraction:float; answer_positive:bool; counterfactual_gold:bool|None=None; temporal_gold:bool|None=None; inhibitor_gold:bool|None=None; binding_gold:bool|None=None; revision_expected:bool=False
    def runtime_record(self):
        return {'episode_id':self.episode_id,'candidates':[{'name':c.name,'features':(c.explained,c.contradictions,c.heldout,c.complexity,c.symmetry_signal,c.chain_signal,c.inverse_signal,c.blocker_signal)} for c in self.candidates]}
    def scorer_record(self):
        return asdict(self)

class HardOOSDGenerator:
    def __init__(self,seed=404): self.seed=seed
    def _episode(self,rng,stratum,idx):
        templates=program_templates(); gold=idx%len(templates); gt=topology_fingerprint(templates[gold])
        hidden=rng.uniform(.20,.50) if stratum in {'partial_noisy','mixed_adversarial'} else rng.uniform(0,.08)
        dist=rng.uniform(.10,.30) if stratum in {'partial_noisy','mixed_adversarial'} else rng.uniform(.04,.18)
        noise=rng.uniform(0,.15) if stratum in {'partial_noisy','mixed_adversarial'} else rng.uniform(0,.05)
        unresolved=(stratum=='binding_ambiguity' and idx%4==0)
        candidates=[]
        for j,t in enumerate(templates):
            good=j==gold
            phase=((idx*7+j*11)%17)/16
            explained=.52 + (.06 if good else 0) + .20*(phase-.5) + rng.gauss(0,.10)
            contradictions=.42 + (-.05 if good else 0) + .18*((1-phase)-.5) + rng.gauss(0,.10)
            heldout=.50 + (.07 if good else 0) + .16*(((idx+j*3)%13)/12-.5) + rng.gauss(0,.11)
            complexity=.45 + (.10 if good and stratum in {'novel_ast','mixed_adversarial'} else 0) + rng.gauss(0,.12)
            sig=[.45+rng.gauss(0,.18) for _ in range(4)]
            family=gold%4
            if good: sig[family]+=0.13
            if stratum in {'temporal_inhibitor','counterfactual_traps','mixed_adversarial'} and good: sig[family]-=.08
            vals=[max(0,min(1,x)) for x in (explained,contradictions,heldout,complexity,*sig)]
            candidates.append(DCandidate(f'd_ast_{j}',*vals,topology_fingerprint(t)))
        return HardDEpisode(uuid.UUID(int=rng.getrandbits(128)).hex,stratum,tuple(candidates),gold,gt,'UNRESOLVED' if unresolved else ('TRUE' if idx%2==0 else 'FALSE'),hidden,dist,noise,idx%2==0,
            counterfactual_gold=(idx%3!=0) if stratum in {'counterfactual_traps','mixed_adversarial'} else None,
            temporal_gold=(idx%5!=0) if stratum in {'temporal_inhibitor','mixed_adversarial'} else None,
            inhibitor_gold=(idx%4!=0) if stratum in {'temporal_inhibitor','mixed_adversarial'} else None,
            binding_gold=(not unresolved) if stratum in {'binding_ambiguity','mixed_adversarial'} else None,
            revision_expected=stratum in {'binding_ambiguity','mixed_adversarial'})
    def generate(self,n=None):
        rng=random.Random(0xD00D5EED+self.seed)
        out=[]
        if n is not None:
            strata=list(ALLOCATIONS)
            for i in range(n): out.append(self._episode(rng,strata[i%len(strata)],i))
            return tuple(out)
        k=0
        for s,count in ALLOCATIONS.items():
            for _ in range(count): out.append(self._episode(rng,s,k)); k+=1
        return tuple(out)
