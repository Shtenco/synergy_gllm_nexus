from __future__ import annotations
from dataclasses import dataclass
from ..contracts import ExpertContext,ExpertProposal,CapabilityTag
@dataclass(frozen=True)
class SupportMapping:
    state:int; execute_target:int; analyze_target:int
class R7LFastInductionExpert:
    expert_id='r7l'
    def propose(self,context:ExpertContext):
        sup=tuple(context.support_demonstrations or ())
        if not sup:
            return ExpertProposal('r7l:abstain',self.expert_id,CapabilityTag.FAST_INDUCTION,uncertainty=1.0)
        m=context.meta(); q=int(m.get('query_state',-1)); intent=m.get('intent','execute')
        if q<0 or q>3: return ExpertProposal('r7l:badq',self.expert_id,CapabilityTag.FAST_INDUCTION,uncertainty=1.0,failure_flags=('INVALID_QUERY',))
        vals=[s.execute_target if intent=='execute' else s.analyze_target for s in sup]
        states=[s.state for s in sup]; mapping={s:v for s,v in zip(states,vals)}
        if q in mapping: ans=mapping[q]
        else:
            remain=set(range(4))-set(vals)
            if len(remain)!=1: return ExpertProposal('r7l:amb',self.expert_id,CapabilityTag.FAST_INDUCTION,uncertainty=1.0)
            ans=next(iter(remain))
        return ExpertProposal('r7l:proposal',self.expert_id,CapabilityTag.FAST_INDUCTION,answer_candidates=(ans,),rule_hypotheses=(tuple(sorted(mapping.items())),),confidence=.99,uncertainty=.01,provenance=('support_demonstrations',))
