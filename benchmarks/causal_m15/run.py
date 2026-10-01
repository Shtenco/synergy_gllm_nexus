from __future__ import annotations
from dataclasses import dataclass
import random
from nexus_gllm.unified_v3.cognitive.causal_model import *

@dataclass(frozen=True)
class Case:
    case_id:str
    observational:tuple[CausalEvidence,...]
    interventions:tuple[CausalEvidence,...]
    cause:str
    effect:str
    gold_identified:bool

def generate(seed=2026093021,n=300):
    r=random.Random(seed);out=[]
    for i in range(n):
        a=f'a{i}';b=f'b{i}'
        causal=(i%2)==0
        obs=(CausalEvidence(f'o{i}',a,b,CausalEvidenceKind.OBSERVATIONAL,.95,.95),)
        if causal:
            inter=(CausalEvidence(f'i{i}',a,b,CausalEvidenceKind.INTERVENTIONAL,.9,.95),CausalEvidence(f'c{i}',a,b,CausalEvidenceKind.COUNTERFACTUAL,.7,.9))
        else:
            inter=(CausalEvidence(f'i{i}',a,b,CausalEvidenceKind.INTERVENTIONAL,-.9,.95),)
        out.append(Case(f'C{i}',obs,inter,a,b,causal))
    return tuple(out)

def evaluate(cases,use_interventions=True):
    correct=0;false_causal=0
    for c in cases:
        g=CausalGraph()
        for e in c.observational:g.add(e)
        if use_interventions:
            for e in c.interventions:g.add(e)
        pred=g.edge(c.cause,c.effect).identified
        correct+=int(pred==c.gold_identified)
        false_causal+=int(pred and not c.gold_identified)
    n=max(1,len(cases));return {'accuracy':correct/n,'false_causal_rate':false_causal/n}
