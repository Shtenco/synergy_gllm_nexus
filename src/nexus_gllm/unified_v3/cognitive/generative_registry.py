from __future__ import annotations
from dataclasses import dataclass
from .generative_admission import *
@dataclass(frozen=True)
class RegisteredGenerativeCortex:
    spec:GenerativeArtifactSpec
    metrics:GenerativeEvalMetrics
    active:bool=False
class GenerativeCortexRegistry:
    def __init__(self,gate=None):self.gate=gate or GenerativeCortexAdmissionGate();self._models={}
    def register(self,spec,metrics):
        d=self.gate.decide(spec,metrics);self._models[spec.model_id]=RegisteredGenerativeCortex(spec,metrics,d.admitted);return d
    def active(self):return tuple(x for x in self._models.values() if x.active)
    def get(self,model_id):return self._models[model_id]
