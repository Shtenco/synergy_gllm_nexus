from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence
import hashlib, time

from .r13x import Proposal, R13XEngine, Blackboard, _AUTHORITY
from .unified_v3.contracts import WorldHypothesis, WorldFact, Intervention, InterventionKind
from .unified_v3.counterfactual import CounterfactualEngine
from .unified_v3.epistemic import EpistemicController

@dataclass(frozen=True)
class R13XTrace:
    stage: str
    detail: str = ""
    elapsed_ms: float = 0.0

@dataclass(frozen=True)
class R13XResult:
    answer: Proposal | None
    proposals: tuple[Proposal, ...]
    traces: tuple[R13XTrace, ...]
    counterfactual_changed: bool = False
    epistemic_state: str = "UNRESOLVED"
    world_consistent: bool = True
    replay_hash: str = ""

class EvidenceRouter:
    """Separates capability routing from evidence quality."""
    def score(self, p: Proposal) -> float:
        authority = _AUTHORITY.get(p.verification or "SURFACE_GUESS", 1)
        evidence = min(1.0, len(p.evidence) / 3.0)
        provenance = min(1.0, len(p.provenance) / 2.0)
        return authority * 10.0 + p.confidence * 2.0 + evidence + provenance - p.uncertainty

class VerifierRouter:
    def attacks(self, proposals: Sequence[Proposal]) -> tuple[str, ...]:
        ops = set()
        for p in proposals:
            if p.verification_op: ops.add(p.verification_op)
        return tuple(sorted(ops | {"EXACT_ASSERT"}))

class WorldConsistency:
    def check(self, world: WorldHypothesis, proposal: Proposal) -> bool:
        if proposal.metadata.get("world_consistent") is False: return False
        return True

class R13XUnifiedV3:
    """Adapter that turns Unified V3 world/counterfactual/epistemic primitives into R1.3-X governance."""
    def __init__(self):
        self.engine=R13XEngine()
        self.evidence_router=EvidenceRouter()
        self.verifier_router=VerifierRouter()
        self.counterfactual=CounterfactualEngine()
        self.epistemic=EpistemicController()
        self.world_check=WorldConsistency()

    @staticmethod
    def _hash(obj: Any) -> str:
        return hashlib.sha256(repr(obj).encode("utf-8")).hexdigest()

    def answer(self, query: str, proposals: Sequence[Proposal], *,
               world: WorldHypothesis | None = None,
               interventions: Sequence[Intervention] = ()) -> R13XResult:
        t0=time.perf_counter(); traces=[]
        board=Blackboard()
        ordered=tuple(sorted(proposals,key=lambda p:(-self.evidence_router.score(p),p.expert_id)))
        traces.append(R13XTrace("route", ",".join(p.expert_id for p in ordered), (time.perf_counter()-t0)*1000))
        board.extend(ordered)
        verified=tuple(self.engine.verifier.verify(p) for p in board.snapshot())
        traces.append(R13XTrace("verify",str(len(verified)),(time.perf_counter()-t0)*1000))
        if world is not None:
            cf=world if not interventions else self.counterfactual.apply(world,tuple(interventions))
            changed=cf != world
            traces.append(R13XTrace("counterfactual", "changed" if changed else "stable",(time.perf_counter()-t0)*1000))
        else:
            changed=False
        consistent=all(self.world_check.check(world,p) for p in verified) if world else True
        candidates=tuple(p for p in verified if consistent or p.metadata.get("world_consistent") is not False)
        answer=self.engine.governor.resolve(candidates)
        state="UNRESOLVED"
        truths=[]
        for p in candidates:
            if isinstance(p.value,bool): truths.append(type("R",(),{"truth":p.value})())
        if truths: state=self.epistemic.resolve(truths).state.value
        traces.append(R13XTrace("govern", "answer" if answer else "abstain",(time.perf_counter()-t0)*1000))
        replay=self._hash((query,tuple(verified),world,tuple(interventions),answer))
        return R13XResult(answer,verified,tuple(traces),changed,state,consistent,replay)
