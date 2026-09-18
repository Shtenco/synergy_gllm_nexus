from nexus_gllm.unified_v3.moe.contracts import *
from nexus_gllm.unified_v3.moe.experts.base import SafeExpertRunner
from nexus_gllm.unified_v3.moe.experts.v3_hypothesis import V3HypothesisExpert
from nexus_gllm.unified_v3.moe.runtime import UnifiedNexusV3MoE
from nexus_gllm.unified_v3.moe.registry_defaults import build_default_registry
class Boom:
    def propose(self,ctx): raise RuntimeError('x')
def test_safe_runner_converts_exception_to_failed_abstention():
    spec=ExpertSpec('boom','1',(CapabilityTag.PROOF,), 'g',None,None,'x')
    p=SafeExpertRunner().run(spec,Boom(),ExpertContext())
    assert p.answer_candidates==() and 'EXCEPTION' in p.failure_flags
def test_v3_native_expert_preserves_multiple_rule_hypotheses():
    p=V3HypothesisExpert().propose(ExpertContext(metadata={'candidate_rules':['TRANSITIVE','SYMMETRIC']}))
    assert len(p.rule_hypotheses)==2
def test_default_registry_has_primary_active_and_remaining_shadow():
    reg=build_default_registry(); active={x.expert_id for x in reg.active()}; shadow={x.expert_id for x in reg.shadow()}
    assert {'r7l','r72','r718','r744','graph','v3'}.issubset(active)
    assert {'r76','r78','r710','r714','v10','unified_r13','v30'}.issubset(shadow)
def test_moe_runtime_routes_topk_and_fuses_answer():
    moe=UnifiedNexusV3MoE(); ctx=ExpertContext(metadata={'evidence':[('s1','q',True)],'candidate_rules':['DIRECT'],'expert_answers':{'r718':'YES','v3':'YES'}})
    out=moe.respond(ctx); assert 2<=len(out.routing.selected_experts)<=4 and out.fused.leading_answer=='YES' and out.authority=='v3_epistemic'
