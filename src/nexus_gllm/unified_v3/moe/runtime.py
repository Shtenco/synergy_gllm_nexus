from dataclasses import dataclass,replace
from .contracts import *
from .registry_defaults import build_default_registry
from .capability_router import RouterFeatures
from .learned_router import LoadableCapabilityRouter
from .novelty_gate import NoveltyGate,NoveltySignals
from .proposal_fusion import ProposalFusion
from .experts.base import SafeExpertRunner
from .experts.r7l_fast_induction import R7LFastInductionExpert
from .experts.r72_language import R72LanguageExpert
from .experts.r718_evidence import R718EvidenceExpert
from .experts.r744_context import R744ContextExpert
from .experts.omega15r2_graph import Omega15R2GraphExpert
from .experts.v3_hypothesis import V3HypothesisExpert
@dataclass(frozen=True)
class MoEResponse:
    routing:RoutingDecision; proposals:tuple[ExpertProposal,...]; fused:FusedProposalSet; authority:str='v3_epistemic'; novelty_state:str='KNOWN'; router_source:str='heuristic_fallback'; router_reason:str=''
class UnifiedNexusV3MoE:
    def __init__(self,router_artifact_dir=None):
        self.registry=build_default_registry(); self.router=LoadableCapabilityRouter(router_artifact_dir); self.novelty=NoveltyGate(); self.fusion=ProposalFusion(); self.runner=SafeExpertRunner()
        self.adapters={'r7l':R7LFastInductionExpert(),'r72':R72LanguageExpert(),'r718':R718EvidenceExpert(),'r744':R744ContextExpert(),'graph':Omega15R2GraphExpert(),'v3':V3HypothesisExpert()}
    def _features(self,ctx):
        m=ctx.meta(); ev=tuple(m.get('evidence',())); conflict=len({x[2] for x in ev if len(x)>=3})>1
        return RouterFeatures(len(ctx.support_demonstrations or ()),m.get('language','ru' if m.get('text') else ''),conflict,len(m.get('events',())),1.0 if m.get('subject') and m.get('relation') else 0.0,1.0 if m.get('candidate_rules') else 0.0,float(m.get('novelty',0.0)),float(m.get('cost_signal',0.0)))
    def respond(self,ctx:ExpertContext):
        f=self._features(ctx); routing=self.router.route(f,self.registry,2,4)
        ns=NoveltySignals(.8,.2,float(ctx.meta().get('novelty',0)),float(ctx.meta().get('ast_novelty',0)),0.2,bool(ctx.support_demonstrations)); nd=self.novelty.classify(ns)
        selected=list(routing.selected_experts)
        for e in nd.required_experts:
            if e not in selected and e in self.adapters: selected.append(e)
        selected=selected[:4]; routing=RoutingDecision(tuple(selected),routing.scores,len(selected)>len(routing.selected_experts))
        proposals=[]; answers=ctx.meta().get('expert_answers',{})
        for eid in selected:
            p=self.runner.run(self.registry.get(eid),self.adapters[eid],ctx)
            if eid in answers and not p.answer_candidates: p=replace(p,answer_candidates=(answers[eid],),confidence=max(p.confidence,.9),uncertainty=min(p.uncertainty,.1))
            proposals.append(p)
        fused=self.fusion.fuse(tuple(proposals),self.registry)
        st=self.router.status
        return MoEResponse(routing,tuple(proposals),fused,'v3_epistemic',nd.state.value,st.source,st.reason)
