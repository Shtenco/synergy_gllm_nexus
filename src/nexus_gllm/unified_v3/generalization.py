from dataclasses import dataclass
from .contracts import GeneralizationAudit
@dataclass(frozen=True)
class InterventionCheck: result: object; expected_change: bool=True
class GeneralizationGovernor:
    def audit(self,base,variants,interventions=()):
        inv=sum(1 for v in variants if v.truth==base.truth)/len(variants) if variants else 1.0
        checked=[i for i in interventions if i.expected_change]; sens=sum(1 for i in checked if i.result.truth!=base.truth)/len(checked) if checked else 1.0
        violations=[]
        if inv<1.0: violations.append('invariance_failure')
        if sens<1.0: violations.append('intervention_collapse')
        return GeneralizationAudit(not violations,inv,sens,tuple(violations),(inv+sens)/2)
    def hypothesis_stability(self,a,b):
        return 1.0 if tuple(a)==tuple(b) else (len(set(a)&set(b))/max(len(set(a)|set(b)),1))
