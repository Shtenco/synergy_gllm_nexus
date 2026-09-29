from nexus_gllm.unified_v3.cognitive.action_boundary import *
def proposal(risk=ActionRisk.LOW,cost=1.0):
    return ActionProposal('email.send','gmail:recipient',( ('subject','hello'), ),'send approved summary',('ev1',),risk,cost,'gmail.send')
def permit(p,**kw):
    x=dict(proposal_sha256=p.proposal_sha256,issuer='META-OS',policy_id='policy:v1',allowed_action_types=('email.send',),allowed_scopes=('gmail.send',),max_risk=ActionRisk.MEDIUM,max_cost=5.0,approval_refs=('user:approval:1',))
    x.update(kw);return ExecutionPermit(**x)
def test_nexus_action_without_permit_is_denied():
    p=proposal();d=ActionBoundary().authorize(p,None);assert not d.authorized and 'permit_missing' in d.reasons
def test_permit_is_bound_to_exact_proposal_hash():
    p=proposal();q=proposal(cost=2.0);d=ActionBoundary().authorize(q,permit(p));assert not d.authorized and 'proposal_hash_mismatch' in d.reasons
def test_scope_and_action_type_are_both_required():
    p=proposal();d=ActionBoundary().authorize(p,permit(p,allowed_scopes=('drive.write',)));assert not d.authorized and 'scope_not_allowed' in d.reasons
def test_high_risk_requires_explicit_approval():
    p=proposal(ActionRisk.HIGH);d=ActionBoundary().authorize(p,permit(p,max_risk=ActionRisk.HIGH,approval_refs=()));assert not d.authorized and 'explicit_approval_required' in d.reasons
def test_valid_permit_only_packages_for_external_executor():
    p=proposal();a=ActionBoundary().package(p,permit(p));assert a.authorization.authorized and a.execution_authority=='AUTOPILOT_OR_META_OS'
