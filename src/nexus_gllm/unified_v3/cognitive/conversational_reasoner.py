from __future__ import annotations
from dataclasses import dataclass

from nexus_gllm.unified_v3.contracts import EpistemicResult,EpistemicState
from .conversation_shell import ConversationShellR1
from .task_cortex import TaskCortexPort,ControlledTaskBackend,TaskParseResult
from .program_synthesis import ProgramSynthesisCortex,ProgramEvidenceCase,ProgramSynthesisResult
from .cognitive_loop import CognitiveLoopR1,CognitiveRequest,CognitiveDecision
from .generative import SafeSurfaceResult


@dataclass(frozen=True)
class ConversationalReasoningResult:
    task:TaskParseResult
    synthesis:ProgramSynthesisResult|None
    decision:CognitiveDecision|None
    epistemic:EpistemicResult
    surface:SafeSurfaceResult


class ConversationalReasonerR1:
    """Controlled end-to-end path with no target gold/program injection."""
    def __init__(self,shell:ConversationShellR1,*,task_backend=None,program_cortex=None,cognitive_loop=None):
        self.shell=shell
        self.task_cortex=TaskCortexPort(task_backend or ControlledTaskBackend())
        self.program_cortex=program_cortex or ProgramSynthesisCortex()
        self.loop=cognitive_loop or CognitiveLoopR1()

    @staticmethod
    def _epistemic_from_decision(decision):
        if decision is None:
            return EpistemicResult(EpistemicState.UNRESOLVED,(),0.0)
        truth=decision.execution.execution.truth
        if truth is True:return EpistemicResult(EpistemicState.PROVED,('да',),.9,1.0,0.0,0.0)
        if truth is False:return EpistemicResult(EpistemicState.DISPROVED,('нет',),.9,0.0,1.0,0.0)
        return EpistemicResult(EpistemicState.UNRESOLVED,(),.2,0.0,0.0,1.0)

    def answer(self,text,*,program_evidence=(),novelty=.5,uncertainty=.5,capability_hints=('program_execution',)):
        task=self.task_cortex.parse(text)
        if task.task is None:
            ep=EpistemicResult(EpistemicState.UNRESOLVED,(),0.0)
            return ConversationalReasoningResult(task,None,None,ep,self.shell.render(ep))

        synthesis=self.program_cortex.synthesize(self.shell.world,task.task,tuple(program_evidence))
        if synthesis.selected is None:
            ep=EpistemicResult(EpistemicState.UNRESOLVED,(),0.0)
            return ConversationalReasoningResult(task,synthesis,None,ep,self.shell.render(ep))

        req=CognitiveRequest(
            episode_id='conversation-query:'+task.input_sha256[:16],
            world=self.shell.world,
            task=task.task,
            program=synthesis.selected,
            novelty=float(novelty),
            uncertainty=float(uncertainty),
            capability_hints=tuple(capability_hints),
        )
        decision=self.loop.deliberate(req)
        ep=self._epistemic_from_decision(decision)
        surface=self.shell.render(ep)
        return ConversationalReasoningResult(task,synthesis,decision,ep,surface)
