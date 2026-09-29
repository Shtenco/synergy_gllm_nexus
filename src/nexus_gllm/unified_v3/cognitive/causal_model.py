from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import math

class CausalEvidenceKind(str,Enum):
    OBSERVATIONAL='OBSERVATIONAL'
    INTERVENTIONAL='INTERVENTIONAL'
    COUNTERFACTUAL='COUNTERFACTUAL'

@dataclass(frozen=True)
class CausalEvidence:
    evidence_id:str
    cause:str
    effect:str
    kind:CausalEvidenceKind
    support:float
    trust:float=1.0
    intervention_value:str|None=None
    outcome_value:str|None=None

@dataclass(frozen=True)
class CausalEdge:
    cause:str
    effect:str
    observational_mass:float
    interventional_mass:float
    counterfactual_mass:float
    contradiction_mass:float
    confidence:float
    identified:bool

class CausalGraph:
    """Evidence-weighted causal graph that never promotes correlation alone."""
    def __init__(self,min_interventional_mass=.75,min_total_causal_mass=1.0):
        self.min_interventional_mass=float(min_interventional_mass)
        self.min_total_causal_mass=float(min_total_causal_mass)
        self._evidence:dict[tuple[str,str],list[CausalEvidence]]=defaultdict(list)

    def add(self,e:CausalEvidence):
        if e.cause==e.effect:raise ValueError('self-causal edge not allowed')
        if not -1<=e.support<=1:raise ValueError('support must be in [-1,1]')
        if not 0<=e.trust<=1:raise ValueError('trust must be in [0,1]')
        self._evidence[(e.cause,e.effect)].append(e);return self

    def edge(self,cause,effect)->CausalEdge:
        rows=tuple(self._evidence.get((cause,effect),()))
        obs=inter=cf=contra=0.0
        for e in rows:
            mass=abs(e.support)*e.trust
            if e.support<0:contra+=mass;continue
            if e.kind is CausalEvidenceKind.OBSERVATIONAL:obs+=mass
            elif e.kind is CausalEvidenceKind.INTERVENTIONAL:inter+=mass
            else:cf+=mass
        causal=inter+cf
        total=obs+causal+contra
        confidence=0.0 if total<=0 else max(0.0,min(1.0,(causal+0.25*obs-contra)/total))
        identified=inter>=self.min_interventional_mass and causal>=self.min_total_causal_mass and causal>contra
        return CausalEdge(cause,effect,obs,inter,cf,contra,confidence,identified)

    def parents(self,effect,*,identified_only=True):
        out=[]
        for cause,e in sorted(self._evidence):
            if e!=effect:continue
            edge=self.edge(cause,effect)
            if not identified_only or edge.identified:out.append(edge)
        return tuple(out)

    def descendants(self,cause):
        seen=set();front=[cause]
        while front:
            x=front.pop(0)
            for (a,b) in self._evidence:
                if a!=x:continue
                if not self.edge(a,b).identified:continue
                if b not in seen:seen.add(b);front.append(b)
        seen.discard(cause);return tuple(sorted(seen))

    def would_cycle(self,cause,effect):
        return cause==effect or cause in self.descendants(effect)


@dataclass(frozen=True)
class InterventionRecord:
    variable:str
    value:str
    observed_effects:tuple[tuple[str,str],...]
    evidence_id:str

class InterventionLedger:
    def __init__(self):self._rows=[]
    def record(self,variable,value,observed_effects,evidence_id):
        r=InterventionRecord(variable,value,tuple(observed_effects),evidence_id);self._rows.append(r);return r
    def rows(self):return tuple(self._rows)
    def to_evidence(self,effect_variable,positive_outcome):
        out=[]
        for r in self._rows:
            for var,val in r.observed_effects:
                if var!=effect_variable:continue
                support=1.0 if val==positive_outcome else -1.0
                out.append(CausalEvidence(r.evidence_id,r.variable,effect_variable,CausalEvidenceKind.INTERVENTIONAL,support,1.0,r.value,val))
        return tuple(out)
