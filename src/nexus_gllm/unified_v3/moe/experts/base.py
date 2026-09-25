from ..contracts import ExpertProposal,ExpertFailureFlag,ExpertMode
class SafeExpertRunner:
    def run(self,spec,adapter,context):
        if spec.active_mode is ExpertMode.DISABLED:
            return ExpertProposal(f'{spec.expert_id}:disabled',spec.expert_id,spec.capability_tags[0],failure_flags=('DISABLED',))
        try:
            p=adapter.propose(context)
            if not isinstance(p,ExpertProposal) or p.expert_id!=spec.expert_id:
                return ExpertProposal(f'{spec.expert_id}:malformed',spec.expert_id,spec.capability_tags[0],failure_flags=(ExpertFailureFlag.MALFORMED.value,))
            return p
        except Exception:
            return ExpertProposal(f'{spec.expert_id}:exception',spec.expert_id,spec.capability_tags[0],failure_flags=(ExpertFailureFlag.EXCEPTION.value,))
