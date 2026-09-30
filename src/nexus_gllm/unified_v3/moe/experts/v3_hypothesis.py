from ..contracts import ExpertContext,ExpertProposal,CapabilityTag
class V3HypothesisExpert:
    expert_id='v3'
    def propose(self,context:ExpertContext):
        m=context.meta(); rules=tuple(m.get('candidate_rules',())); ans=m.get('expert_answers',{}).get(self.expert_id)
        return ExpertProposal('v3:proposal',self.expert_id,CapabilityTag.HYPOTHESIS,rule_hypotheses=rules,answer_candidates=((ans,) if ans is not None else ()),confidence=.92 if rules or ans is not None else .35,uncertainty=.08 if rules or ans is not None else .65,provenance=('native_v3',))
