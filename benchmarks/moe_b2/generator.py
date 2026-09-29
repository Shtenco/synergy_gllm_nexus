from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,random
EXPERTS=('r7l','r72','r718','r744','graph','v3')
FEATURES=('support','ru','evidence','context','graph','novelty','proof','cost')
STRATA=('cross_capability','cue_conflict','open_set','cost_pressure','composition_shift','adversarial_mixture')
@dataclass(frozen=True)
class B2RuntimeCase: case_id:str;features:tuple[float,...];stratum:str
@dataclass(frozen=True)
class B2Gold: case_id:str;useful:tuple[str,...];harmful:tuple[str,...];utility:tuple[float,...];should_abstain:bool
@dataclass(frozen=True)
class B2Bundle: runtime:tuple[B2RuntimeCase,...];gold:tuple[B2Gold,...]
def _id(seed,i):return hashlib.sha256(f'B2:{seed}:{i}'.encode()).hexdigest()[:24]
def _clip(x):return max(0.0,min(1.0,float(x)))
def _utility(x,stratum,rng):
    support,ru,evidence,context,graph,novelty,proof,cost=x;u=[0.0]*6
    u[0]=1.55*support+.85*novelty+.55*support*novelty-.50*cost
    u[1]=1.35*ru+.50*graph+.35*ru*context-.35*cost
    u[2]=1.45*evidence+.70*proof+.65*evidence*novelty-.40*cost
    u[3]=1.30*context+.55*ru+.55*context*novelty-.30*cost
    u[4]=1.40*graph+.55*ru+.75*graph*proof-.45*cost
    u[5]=1.00*novelty+.70*proof+.65*context+.70*novelty*proof-.55*cost
    if stratum=='cue_conflict':
        lure=max(range(6),key=lambda j:u[j]);u[lure]-=1.15;u[(lure+3)%6]+=.35
    elif stratum=='open_set':u=[z-1.20 for z in u];u[5]-=.25
    elif stratum=='cost_pressure':u=[z-(.25+.12*j)*cost for j,z in enumerate(u)]
    elif stratum=='composition_shift':u[5]+=graph*context+evidence*proof;u[4]+=.55*graph*context;u[2]+=.45*evidence*proof
    elif stratum=='adversarial_mixture':u=[z+(.35 if j%2==(int(10*novelty)%2) else -.35) for j,z in enumerate(u)]
    return tuple(z+rng.gauss(0,.02) for z in u)
def generate(seed=2026093001,n_per_stratum=400):
    rng=random.Random(seed);runtime=[];gold=[];i=0
    for sidx,stratum in enumerate(STRATA):
        for _ in range(n_per_stratum):
            vals=[]
            for j in range(8):
                if (i+j+sidx)%3==0:v=rng.betavariate(.55,2.4)
                elif (i+j+sidx)%3==1:v=rng.betavariate(2.4,.55)
                else:v=rng.random()
                vals.append(_clip(v))
            vals[7]=_clip(.15+.8*rng.random());x=tuple(vals);util=_utility(x,stratum,rng);order=sorted(range(6),key=lambda j:(-util[j],j));best=util[order[0]];second=util[order[1]]
            abstain=(stratum=='open_set' and best<.55) or best<.35 or (best-second<.025 and x[5]>.75)
            useful=tuple(EXPERTS[j] for j in order[:2] if util[j]>.35);harmful=tuple(EXPERTS[j] for j in order[-2:] if util[j]<.15);cid=_id(seed,i)
            runtime.append(B2RuntimeCase(cid,x,stratum));gold.append(B2Gold(cid,useful,harmful,util,abstain));i+=1
    order=list(range(len(runtime)));rng.shuffle(order);return B2Bundle(tuple(runtime[k] for k in order),tuple(gold[k] for k in order))
def runtime_jsonl(bundle):return '\n'.join(json.dumps({'case_id':c.case_id,'features':dict(zip(FEATURES,c.features)),'stratum':c.stratum},sort_keys=True,separators=(',',':')) for c in bundle.runtime)+'\n'
def gold_jsonl(bundle):
    by={g.case_id:g for g in bundle.gold}
    return '\n'.join(json.dumps({'case_id':c.case_id,'useful':by[c.case_id].useful,'harmful':by[c.case_id].harmful,'utility':by[c.case_id].utility,'should_abstain':by[c.case_id].should_abstain},sort_keys=True,separators=(',',':')) for c in bundle.runtime)+'\n'
