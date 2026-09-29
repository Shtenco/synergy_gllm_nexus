from __future__ import annotations
from pathlib import Path
from .evaluate import Route
from .generator import FEATURES
from nexus_gllm.unified_v3.moe.capability_router import RouterFeatures
from nexus_gllm.unified_v3.moe.learned_router import LoadableCapabilityRouter
from nexus_gllm.unified_v3.moe.registry_defaults import build_default_registry

class FrozenP1B2Adapter:
    """Expose the frozen six-expert P1 router to the sealed B2 runtime.

    No scorer-only gold is accepted by this object.
    """
    def __init__(self,artifact_dir=None,*,abstain_novelty=.80,abstain_top_probability=.55):
        self.router=LoadableCapabilityRouter(artifact_dir)
        if not self.router.status.loaded:
            raise RuntimeError(f'P1 not verified: {self.router.status.reason}')
        self.registry=build_default_registry()
        self.abstain_novelty=float(abstain_novelty)
        self.abstain_top_probability=float(abstain_top_probability)
    @staticmethod
    def _features(case):
        x=dict(zip(FEATURES,case.features))
        return RouterFeatures(
            support_count=round(4*x['support']),
            language='ru' if x['ru']>=.5 else '',
            evidence_conflict=x['evidence']>=.5,
            context_depth=round(4*x['context']),
            graph_signal=x['graph'],
            proof_signal=x['proof'],
            novelty=x['novelty'],
            cost_signal=x['cost'],
            ru_signal=x['ru'],
            evidence_signal=x['evidence'],
        )
    def route(self,case):
        f=self._features(case)
        d=self.router.route(f,self.registry,2,4)
        novelty=self.router.novelty_probability(f)
        scores=tuple((eid,float(score)) for eid,score in d.scores)
        top=max((s for _,s in scores),default=0.0)
        abstain=bool(novelty is not None and novelty>=self.abstain_novelty and top<self.abstain_top_probability)
        return Route(tuple(d.selected_experts),scores,abstain)
