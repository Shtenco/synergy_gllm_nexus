from ..contracts import ExpertProposal,CapabilityTag
class ShadowAdapter:
    def __init__(self,expert_id='v10_procedural'): self.expert_id=expert_id
    def propose(self,context): return ExpertProposal(self.expert_id+':shadow',self.expert_id,CapabilityTag.HYPOTHESIS,uncertainty=1.0,provenance=('shadow_only',))
