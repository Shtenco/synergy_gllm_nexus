from __future__ import annotations

import hashlib

from nexus_gllm.unified_v3.contracts import EpistemicState, TaskOpcode
from nexus_gllm.unified_v3.cognitive.conversation_shell import ConversationShellR1
from nexus_gllm.unified_v3.cognitive.conversational_reasoner import ConversationalReasonerR1
from nexus_gllm.unified_v3.cognitive.conversational_reasoner_r2 import (
    ConversationalReasonerR2,
    ConversationalRequest,
)
from nexus_gllm.unified_v3.cognitive.generalized_ingress import (
    GeneralizedIngressProposal,
    GeneralizedIngressR1,
    GeneralizedSemanticAtomProposal,
    GeneralizedTaskProposal,
    GroundedSpanRef,
)
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.cognitive.program_proposal import ProgramProposal


def full_span(source):
    return GroundedSpanRef(source.source_id,0,len(source.text),hashlib.sha256(source.text.encode()).hexdigest())


class FixtureBackend:
    backend_id='m32-r2-fixture'
    def __init__(self,*,with_program=True,bad_task=False):
        self.with_program=with_program; self.bad_task=bad_task
    def propose(self,request):
        prompt=request.sources[0]
        evidence=request.sources[1:] or (prompt,)
        atoms=[]
        pairs=(('alice','bob'),('bob','carol'))
        for i,(a,b) in enumerate(pairs):
            src=evidence[min(i,len(evidence)-1)]
            atoms.append(GeneralizedSemanticAtomProposal('parent',(a,b),True,.99,(full_span(src),)))
        task=GeneralizedTaskProposal(
            TaskOpcode.QUERY_RELATION,
            None if self.bad_task else 'parent',
            () if self.bad_task else ('alice','carol'),
            .99 if not self.bad_task else .1,
            (full_span(prompt),),
        )
        program=None
        if self.with_program:
            program=ProgramProposal(
                ProgramNode(ProgramKind.ATOM,'rule:transitive:parent'),
                .99,
                (full_span(prompt),),
            )
        return GeneralizedIngressProposal(self.backend_id,tuple(atoms),task,program)


def make_reasoner(**backend_kwargs):
    shell=ConversationShellR1('m32-r2-test')
    ingress=GeneralizedIngressR1(FixtureBackend(**backend_kwargs))
    return shell,ConversationalReasonerR2(shell,ingress=ingress)


def test_free_russian_request_reaches_crc_and_proves_answer_from_asserted_context():
    shell,r=make_reasoner()
    req=ConversationalRequest('Докажи, является ли Алиса предком Кэрол.',history=('Алиса родитель Боба.',),documents=('Боб родитель Кэрол.',))
    out=r.answer(req)
    assert out.ingress.task is not None
    assert out.program_admission is not None and out.program_admission.accepted
    assert out.decision is not None
    assert out.epistemic.state is EpistemicState.PROVED
    assert out.decision.execution.execution.truth is True
    assert shell.world.facts==()
    assert len(out.context.execution_world.facts)==2


def test_free_english_request_uses_same_typed_path():
    shell,r=make_reasoner()
    out=r.answer(ConversationalRequest('Is Alice an ancestor of Carol?',history=('Alice is parent of Bob.',),documents=('Bob is parent of Carol.',)))
    assert out.epistemic.state is EpistemicState.PROVED
    assert out.ingress.task.operator_id=='parent'
    assert shell.world.facts==()


def test_malformed_task_fails_closed_to_unresolved():
    shell,r=make_reasoner(bad_task=True)
    out=r.answer(ConversationalRequest('free text'))
    assert out.epistemic.state is EpistemicState.UNRESOLVED
    assert out.decision is None
    assert shell.world.facts==()


def test_no_admitted_program_and_no_evidence_is_unresolved():
    shell,r=make_reasoner(with_program=False)
    out=r.answer(ConversationalRequest('free text',history=('Alice parent Bob.',),documents=('Bob parent Carol.',)))
    assert out.epistemic.state is EpistemicState.UNRESOLVED
    assert out.decision is None


def test_frozen_r1_still_rejects_uncontrolled_free_text():
    shell=ConversationShellR1('r1-frozen-check')
    out=ConversationalReasonerR1(shell).answer('Is Alice an ancestor of Carol?')
    assert out.epistemic.state is EpistemicState.UNRESOLVED
    assert out.decision is None
