from __future__ import annotations
from dataclasses import replace,dataclass
from .contracts import HypothesisState,HypothesisBeam,RuleProgram
@dataclass(frozen=True)
class EvidenceSignal:
    RuleFamilyName:str; confirmed:bool=True
class HypothesisSearch:
    def __init__(self,beam_width=8): self.beam_width=beam_width
    def seed(self,worlds,rule_programs):
        out=[]
        for wi,w in enumerate(worlds):
            for ri,r in enumerate(rule_programs):
                fam=r.family.value
                complexity=len(r.operators)+len(r.conditions)+len(r.blockers)
                out.append(HypothesisState(f'h:{wi}:{ri}',w,RuleProgram(clauses=(r,)),score=-0.01*complexity,complexity_cost=float(complexity),rule_family=fam))
        out.sort(key=lambda h:(-h.score,h.rule_family))
        return HypothesisBeam(tuple(out[:self.beam_width]),tuple(out[self.beam_width:]))
    def rescore(self,beam,observations,predictions=()):
        hs=[]
        for h in beam.active:
            delta=0.0
            for e in observations:
                if e.RuleFamilyName==h.rule_family: delta += 1.0 if e.confirmed else -2.0
            hs.append(replace(h,score=h.score+delta,evidence_mass=h.evidence_mass+max(delta,0.0),contradiction_cost=h.contradiction_cost+max(-delta,0.0)))
        hs.sort(key=lambda h:(-h.score,h.complexity_cost,h.rule_family))
        return HypothesisBeam(tuple(hs[:self.beam_width]),beam.eliminated+tuple(hs[self.beam_width:]))
