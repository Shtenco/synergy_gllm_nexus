from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib,json,re

class ActionRisk(str,Enum):
    READ_ONLY='READ_ONLY'
    LOW='LOW'
    MEDIUM='MEDIUM'
    HIGH='HIGH'

@dataclass(frozen=True)
class ActionProposal:
    action_type:str
    target:str
    arguments:tuple[tuple[str,str],...]=()
    reason:str=''
    evidence_ids:tuple[str,...]=()
    risk:ActionRisk=ActionRisk.LOW
    estimated_cost:float=0.0
    requested_scope:str=''
    def canonical(self):
        return {
            'action_type':self.action_type,
            'target':self.target,
            'arguments':list(sorted(self.arguments)),
            'reason':self.reason,
            'evidence_ids':list(sorted(self.evidence_ids)),
            'risk':self.risk.value,
            'estimated_cost':float(self.estimated_cost),
            'requested_scope':self.requested_scope,
        }
    @property
    def proposal_sha256(self):
        b=json.dumps(self.canonical(),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
        return hashlib.sha256(b).hexdigest()

@dataclass(frozen=True)
class ExecutionPermit:
    proposal_sha256:str
    issuer:str
    policy_id:str
    allowed_action_types:tuple[str,...]
    allowed_scopes:tuple[str,...]
    max_risk:ActionRisk
    max_cost:float
    approval_refs:tuple[str,...]=()

@dataclass(frozen=True)
class ActionAuthorization:
    authorized:bool
    reasons:tuple[str,...]
    proposal_sha256:str

@dataclass(frozen=True)
class AuthorizedAction:
    proposal:ActionProposal
    permit:ExecutionPermit
    authorization:ActionAuthorization
    execution_authority:str='AUTOPILOT_OR_META_OS'

class ActionBoundary:
    """NEXUS proposes. AUTOPILOT/META-OS authorizes and executes."""
    RISK_ORDER={ActionRisk.READ_ONLY:0,ActionRisk.LOW:1,ActionRisk.MEDIUM:2,ActionRisk.HIGH:3}
    def authorize(self,proposal:ActionProposal,permit:ExecutionPermit|None)->ActionAuthorization:
        reasons=[]
        if permit is None:
            return ActionAuthorization(False,('permit_missing',),proposal.proposal_sha256)
        if permit.proposal_sha256!=proposal.proposal_sha256:reasons.append('proposal_hash_mismatch')
        if not permit.issuer:reasons.append('issuer_missing')
        if not permit.policy_id:reasons.append('policy_missing')
        if proposal.action_type not in permit.allowed_action_types:reasons.append('action_type_not_allowed')
        if proposal.requested_scope not in permit.allowed_scopes:reasons.append('scope_not_allowed')
        if self.RISK_ORDER[proposal.risk]>self.RISK_ORDER[permit.max_risk]:reasons.append('risk_above_permit')
        if proposal.estimated_cost<0 or proposal.estimated_cost>permit.max_cost:reasons.append('cost_above_permit')
        if proposal.risk in (ActionRisk.MEDIUM,ActionRisk.HIGH) and not permit.approval_refs:reasons.append('explicit_approval_required')
        if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}',proposal.action_type):reasons.append('bad_action_type')
        return ActionAuthorization(not reasons,tuple(sorted(set(reasons))),proposal.proposal_sha256)

    def package(self,proposal:ActionProposal,permit:ExecutionPermit|None)->AuthorizedAction:
        auth=self.authorize(proposal,permit)
        if not auth.authorized:
            raise PermissionError('action authorization denied: '+','.join(auth.reasons))
        return AuthorizedAction(proposal,permit,auth)
