from __future__ import annotations

from dataclasses import dataclass

from nexus_gllm.unified_v3.contracts import EpistemicResult, EpistemicState
from .cognitive_loop import CognitiveDecision, CognitiveLoopR1, CognitiveRequest
from .conversation_shell import ConversationShellR1
from .conversational_reasoner import ConversationalReasonerR1
from .generalized_ingress import GeneralizedIngressR1, GeneralizedIngressRequest, GeneralizedIngressResult
from .generative import SafeSurfaceResult
from .program_proposal import ProgramAdmission, ProgramProposal, ProgramProposalGate
from .program_synthesis import ProgramEvidenceCase, ProgramSynthesisCortex, ProgramSynthesisResult
from .reasoning_context import ReasoningContextBuilder, ReasoningContextView
from .semantic_authority import SemanticAttestation


@dataclass(frozen=True)
class ConversationalRequest:
    prompt: str
    history: tuple[str, ...] = ()
    documents: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConversationalReasoningResultR2:
    ingress: GeneralizedIngressResult
    context: ReasoningContextView
    program_admission: ProgramAdmission | None
    synthesis: ProgramSynthesisResult | None
    decision: CognitiveDecision | None
    epistemic: EpistemicResult
    surface: SafeSurfaceResult


class ConversationalReasonerR2:
    """Generalized proposal-only ingress feeding the frozen CRC reasoning organs."""

    def __init__(
        self,
        shell: ConversationShellR1,
        *,
        ingress: GeneralizedIngressR1,
        context_builder: ReasoningContextBuilder | None = None,
        program_gate: ProgramProposalGate | None = None,
        program_cortex: ProgramSynthesisCortex | None = None,
        cognitive_loop: CognitiveLoopR1 | None = None,
    ):
        self.shell = shell
        self.ingress = ingress
        self.context_builder = context_builder or ReasoningContextBuilder()
        self.program_gate = program_gate or ProgramProposalGate()
        self.program_cortex = program_cortex or ProgramSynthesisCortex()
        self.loop = cognitive_loop or CognitiveLoopR1()

    @staticmethod
    def _unresolved() -> EpistemicResult:
        return EpistemicResult(EpistemicState.UNRESOLVED, (), 0.0)

    def _early_result(
        self,
        ingress: GeneralizedIngressResult,
        context: ReasoningContextView,
        *,
        admission: ProgramAdmission | None = None,
        synthesis: ProgramSynthesisResult | None = None,
    ) -> ConversationalReasoningResultR2:
        epistemic = self._unresolved()
        return ConversationalReasoningResultR2(
            ingress,
            context,
            admission,
            synthesis,
            None,
            epistemic,
            self.shell.render(epistemic),
        )

    def answer(
        self,
        request: ConversationalRequest,
        *,
        attestations: tuple[SemanticAttestation, ...] = (),
        program_evidence: tuple[ProgramEvidenceCase, ...] = (),
        novelty: float = 0.5,
        uncertainty: float = 0.5,
        capability_hints: tuple[str, ...] = ("program_execution",),
    ) -> ConversationalReasoningResultR2:
        generalized_request = GeneralizedIngressRequest.from_texts(
            request.prompt,
            tuple(request.history),
            tuple(request.documents),
        )
        ingress = self.ingress.parse(generalized_request)
        context = self.context_builder.build(self.shell.world, ingress, tuple(attestations))

        if not ingress.admission.accepted or ingress.task is None:
            return self._early_result(ingress, context)

        program = None
        program_admission = None
        if isinstance(ingress.program, ProgramProposal):
            program_admission = self.program_gate.check(
                ingress.program,
                generalized_request,
                ingress.task,
                context,
            )
            if program_admission.accepted:
                program = ingress.program.node

        synthesis = None
        if program is None and program_evidence:
            synthesis = self.program_cortex.synthesize(
                context.execution_world,
                ingress.task,
                tuple(program_evidence),
            )
            program = synthesis.selected

        if program is None:
            return self._early_result(
                ingress,
                context,
                admission=program_admission,
                synthesis=synthesis,
            )

        prompt_source = ingress.source_map.get("prompt:0")
        episode_suffix = prompt_source.sha256[:16] if prompt_source else "unknown"
        cognitive_request = CognitiveRequest(
            episode_id="conversation-r2:" + episode_suffix,
            world=context.execution_world,
            task=ingress.task,
            program=program,
            novelty=float(novelty),
            uncertainty=float(uncertainty),
            capability_hints=tuple(capability_hints),
        )
        decision = self.loop.deliberate(cognitive_request)
        epistemic = ConversationalReasonerR1._epistemic_from_decision(decision)
        return ConversationalReasoningResultR2(
            ingress,
            context,
            program_admission,
            synthesis,
            decision,
            epistemic,
            self.shell.render(epistemic),
        )
