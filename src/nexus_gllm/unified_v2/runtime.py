from __future__ import annotations

from nexus_gllm.unified_v2.bus import OrganBus
from nexus_gllm.unified_v2.contracts import AnswerGraph, ClaimProposal
from nexus_gllm.unified_v2.guard import SemanticConsistencyGuard
from nexus_gllm.unified_v2.organs.evidence_governor import EvidenceGovernor
from nexus_gllm.unified_v2.organs.surface_decoder import NativeRussianSurfaceDecoderV2
from nexus_gllm.unified_v2.workspace import GraphWorkspace


class UnifiedNexusV2P0:
    """Executable authority-safe v2 prototype.

    P0 provides the sovereign commit/render path. Historical neural donor
    adapters are benchmark-composed separately until their artifact loading
    contracts are unified behind this runtime interface.
    """

    def __init__(self):
        self.workspace = GraphWorkspace()
        self.bus = OrganBus()
        self.governor = EvidenceGovernor()
        self.decoder = NativeRussianSurfaceDecoderV2()
        self.guard = SemanticConsistencyGuard()

    @property
    def trace(self):
        return self.bus.trace()

    def _render_claim(self, claim) -> str:
        graph = AnswerGraph((claim,), (), (), ())
        text = self.decoder.render(graph)
        checked = self.guard.check(graph, text)
        if not checked.ok:
            self.bus.record_reject("surface_guard", ",".join(checked.violations))
            return "Не удалось сформировать семантически согласованный ответ."
        self.bus.record_call("surface_decoder", "faithful")
        return text

    def accept_with_evidence(self, proposal: ClaimProposal, evidence) -> str:
        self.workspace.add_candidate(proposal)
        self.bus.record_call("evidence_governor", proposal.claim_id)
        decision = self.governor.decide(proposal, evidence)
        if decision.status != "accepted":
            self.bus.record_reject("evidence_governor", f"{proposal.claim_id}:{decision.status}")
            return self.decoder.render(AnswerGraph((), (), (), ("Недостаточно подтверждений",)))
        claim = self.workspace.commit_proposal(proposal, authority="evidence_governor")
        self.bus.record_commit("evidence_governor", claim.claim_id)
        return self._render_claim(claim)

    def accept_formal(self, proposal: ClaimProposal) -> str:
        self.workspace.add_candidate(proposal)
        self.bus.record_call("formal_authority", proposal.claim_id)
        claim = self.workspace.commit_proposal(proposal, authority="formal_authority")
        self.bus.record_commit("formal_authority", claim.claim_id)
        return self._render_claim(claim)
