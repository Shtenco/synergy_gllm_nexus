from __future__ import annotations
from .generative import AuthoritySafeGenerativeCortex,DeterministicRussianSurface
from .generative_registry import GenerativeCortexRegistry
class GenerativeBackendSelector:
    """Admitted models may be mounted; otherwise deterministic rendering is mandatory."""
    def __init__(self,registry=None):self.registry=registry or GenerativeCortexRegistry()
    def choose(self,backends):
        admitted={x.spec.model_id for x in self.registry.active()}
        for backend in backends:
            model_id=getattr(getattr(backend,'ref',None),'model_id',None)
            if model_id in admitted:return AuthoritySafeGenerativeCortex(backend)
        return AuthoritySafeGenerativeCortex(DeterministicRussianSurface())
