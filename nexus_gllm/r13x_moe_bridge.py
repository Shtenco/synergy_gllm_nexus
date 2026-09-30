from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
import hashlib, time

from .r13x import Proposal, R13XEngine, Blackboard, _AUTHORITY
from .r13x_unified_v3 import R13XUnifiedV3, R13XResult
from .unified_v3.moe.runtime import UnifiedNexusV3MoE
from .unified_v3.moe.contracts import ExpertContext

@dataclass(frozen=True)
class MoEExecution:
    selected: tuple[str,...]
    proposals: tuple[Proposal,...]
    moe_response: Any
    r13x: R13XResult

class R13XMoEBridge:
    """Runs the real Unified V3 MoE adapters, then passes every hypothesis into R1.3-X."""
    def __init__(self, moe: UnifiedNexusV3MoE|None=None, governance: R13XUnifiedV3|None=None):
        self.moe=moe or UnifiedNexusV3MoE()
        self.governance=governance or R13XUnifiedV3()

    def _convert(self,p: Any) -> Proposal:
        value=p.answer_candidates[0] if p.answer_candidates else None
        verification="DIRECT_EVIDENCE" if p.evidence_items else "NEURAL_PROPOSAL"
        if p.proof_steps: verification="CAUSAL_CONSISTENT"
        return Proposal(
            expert_id=p.expert_id, value=value,
            confidence=float(p.confidence), uncertainty=float(p.uncertainty),
            evidence=tuple(p.evidence_items), provenance=tuple(p.provenance),
            verification=verification,
            metadata={"moe_proposal_id":p.proposal_id,
                      "failure_flags":tuple(p.failure_flags)}
        )

    def answer(self, *, context: ExpertContext, query: str="",
               world=None, interventions=()) -> MoEExecution:
        response=self.moe.respond(context)
        converted=tuple(self._convert(p) for p in response.proposals if p.answer_candidates)
        result=self.governance.answer(query,converted,world=world,interventions=interventions)
        return MoEExecution(response.routing.selected_experts,converted,response,result)
