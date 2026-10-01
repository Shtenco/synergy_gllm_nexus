from __future__ import annotations
from dataclasses import dataclass
from .generative import SurfaceContract,AuthoritySafeGenerativeCortex,DeterministicRussianSurface
from nexus_gllm.unified_v3.contracts import EpistemicResult,EpistemicState

def contract_from_epistemic(result:EpistemicResult,*,entities=(),numbers=(),provenance=(),uncertainty=()):
    allow_negation=result.state is EpistemicState.DISPROVED
    return SurfaceContract(
        result.state,
        tuple(result.answer),
        tuple(entities),
        tuple(numbers),
        tuple(provenance),
        allow_negation,
        tuple(uncertainty),
    )

class CRCGenerativePort:
    """Bridge from authority-owned epistemic result to surface-only generation."""
    def __init__(self,backend=None):
        self.cortex=AuthoritySafeGenerativeCortex(backend or DeterministicRussianSurface())
    def render(self,result:EpistemicResult,**kwargs):
        return self.cortex.realize(contract_from_epistemic(result,**kwargs))
