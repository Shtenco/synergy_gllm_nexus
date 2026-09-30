from ..contracts import ExpertContext,ExpertProposal,CapabilityTag
class R744ContextExpert:
    expert_id='r744'
    def propose(self,context:ExpertContext):
        events=tuple(context.meta().get('events',())); latest={}
        for rel,obj,val,t in sorted(events,key=lambda x:x[3]): latest[(rel,obj)]=(rel,obj,val)
        facts=tuple(latest.values())
        return ExpertProposal('r744:proposal',self.expert_id,CapabilityTag.CONTEXT,semantic_facts=facts,confidence=.98 if facts else 0.0,uncertainty=.02 if facts else 1.0,provenance=('context_revision',))
