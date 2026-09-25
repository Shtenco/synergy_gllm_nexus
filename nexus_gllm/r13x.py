from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class Proposal:
    expert_id: str
    value: Any
    confidence: float
    uncertainty: float
    evidence: tuple[Any, ...] = ()
    provenance: tuple[str, ...] = ()
    verification: str | None = None


_AUTHORITY = {
    "EXACT_VERIFIED": 6,
    "DIRECT_EVIDENCE": 5,
    "CAUSAL_CONSISTENT": 4,
    "MEMORY_SUPPORTED": 3,
    "NEURAL_PROPOSAL": 2,
    "SURFACE_GUESS": 1,
}


class R13XGovernor:
    """Authority-first resolver for the Unified R1.3-X architecture.

    It deliberately separates confidence from authority: a neural proposal
    cannot outrank a verified exact result merely by reporting high confidence.
    """

    def resolve(self, proposals: Sequence[Proposal]) -> Proposal | None:
        if not proposals:
            return None

        verified = [p for p in proposals if p.verification in _AUTHORITY]
        pool = verified if verified else list(proposals)

        def key(p: Proposal) -> tuple[int, float, float, int]:
            authority = _AUTHORITY.get(p.verification or "SURFACE_GUESS", 1)
            return authority, p.confidence, -p.uncertainty, len(p.evidence)

        best = max(pool, key=key)
        if best.uncertainty >= 0.95 and best.verification not in {
            "EXACT_VERIFIED",
            "DIRECT_EVIDENCE",
        }:
            return None
        return best


class R13XRouter:
    """Deterministic shell for a future learned sparse router."""

    def route(self, features: Mapping[str, float], experts: Iterable[str]) -> tuple[str, ...]:
        names = tuple(experts)
        if not names:
            return ()
        # Until learned routing is frozen, keep the router transparent:
        # semantic + exact + evidence are always available.
        mandatory = [x for x in ("semantic", "exact", "evidence") if x in names]
        return tuple(dict.fromkeys(mandatory + list(names)))


class UnifiedR13X:
    def __init__(self, governor: R13XGovernor | None = None, router: R13XRouter | None = None):
        self.governor = governor or R13XGovernor()
        self.router = router or R13XRouter()

    def resolve(self, proposals: Sequence[Proposal]) -> Proposal | None:
        return self.governor.resolve(proposals)
