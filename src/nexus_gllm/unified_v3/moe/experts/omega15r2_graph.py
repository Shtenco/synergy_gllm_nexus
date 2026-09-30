from ..contracts import ExpertContext,ExpertProposal,CapabilityTag
class Omega15R2GraphExpert:
    expert_id='graph'
    def propose(self,context:ExpertContext):
        m=context.meta(); s=m.get('subject'); r=m.get('relation'); o=m.get('object')
        facts=((str(s).casefold(),str(r),str(o).casefold()),) if s and r and o else ()
        return ExpertProposal('graph:proposal',self.expert_id,CapabilityTag.GRAPH,semantic_facts=facts,confidence=.9 if facts else 0.0,uncertainty=.1 if facts else 1.0,provenance=('graph_roles',))
