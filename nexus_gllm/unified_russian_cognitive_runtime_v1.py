from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable

from .r13x_exact_cognitive_ru_v3 import ExactCognitiveRussianRuntimeV3

try:
    from .r13x_hybrid_router import HybridR13XRouter
except Exception:  # optional torch dependency / checkpoint
    HybridR13XRouter = None

@dataclass(frozen=True)
class UnifiedRussianTrace:
    route: str
    route_confidence: float
    route_source: str
    cortex_used: bool
    sovereign_authority: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class UnifiedRussianCognitiveRuntimeV1:
    """Russian orchestration shell over the verified R1.3-X V3 authority runtime.

    Design invariant: an external language cortex may propose wording or a candidate
    answer, but it never becomes final authority by itself. Verified/composed exact
    reasoning, persistent memory/world state and fail-closed abstention stay inside
    the NEXUS runtime.
    """

    def __init__(self, *, artifact_root: str | Path | None = None,
                 memory_path: str | Path | None = None,
                 router_checkpoint: str | Path | None = None,
                 cortex: Callable[[str], str] | None = None):
        self.core = ExactCognitiveRussianRuntimeV3(
            memory_path=memory_path, artifact_root=artifact_root
        )
        self.cortex = cortex
        self.router = None
        if router_checkpoint and HybridR13XRouter is not None:
            self.router = HybridR13XRouter(Path(router_checkpoint))

    def route(self, text: str) -> tuple[str, float, str]:
        if self.router is not None:
            return self.router.route(text)
        return "core", 1.0, "core_fallback"

    def answer(self, text: str, session_id: str = "default") -> dict[str, Any]:
        route, conf, source = self.route(text)
        core_response = self.core.answer(text, session_id)

        if not getattr(core_response, "abstained", False):
            return {
                "response": core_response,
                "trace": UnifiedRussianTrace(
                    route, conf, source, False, "NEXUS_CORE",
                    "verified/core resolution retained"
                ).to_dict(),
            }

        proposal = None
        if self.cortex is not None and route == "language":
            try:
                proposal = self.cortex(text)
            except Exception:
                proposal = None

        return {
            "response": core_response,
            "cortex_proposal": proposal,
            "trace": UnifiedRussianTrace(
                route, conf, source, proposal is not None, "ABSTAIN",
                "cortex proposal is non-sovereign and not promoted to final answer"
            ).to_dict(),
        }
