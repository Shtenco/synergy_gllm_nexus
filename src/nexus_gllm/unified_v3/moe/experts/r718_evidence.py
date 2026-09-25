from ..contracts import ExpertContext,ExpertProposal,CapabilityTag
class R718EvidenceExpert:
    expert_id='r718'
    def propose(self,context:ExpertContext):
        ev=tuple(context.meta().get('evidence',())); vals={bool(x[2]) for x in ev if len(x)>=3}
        flags=('CONFLICTED',) if vals=={True,False} else (); conf=.5 if flags else (.95 if ev else 0.0)
        return ExpertProposal('r718:proposal',self.expert_id,CapabilityTag.EVIDENCE,evidence_items=ev,confidence=conf,uncertainty=1-conf,failure_flags=flags,provenance=tuple(str(x[0]) for x in ev))
