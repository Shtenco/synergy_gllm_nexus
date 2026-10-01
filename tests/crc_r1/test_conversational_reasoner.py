from nexus_gllm.unified_v3.cognitive.conversational_reasoner import ConversationalReasonerR1
from nexus_gllm.unified_v3.cognitive.conversation_shell import ConversationShellR1
from nexus_gllm.unified_v3.cognitive.program_synthesis import ProgramEvidenceCase
from nexus_gllm.unified_v3.contracts import *

def w(name,edges):
    op=OperatorSymbol(name,2)
    return WorldHypothesis(name,tuple(WorldFact(op,(Entity(a),Entity(b)),True) for a,b in edges))

def demos():
    return (
      ProgramEvidenceCase(w('r',( ('a','b'),('b','c') )),TaskProgram(TaskOpcode.QUERY_RELATION,'r',('a','c')),True),
      ProgramEvidenceCase(w('r',( ('d','e'),('e','f') )),TaskProgram(TaskOpcode.QUERY_RELATION,'r',('d','f')),True),
    )

def test_controlled_russian_query_executes_without_target_gold_or_ready_program():
    shell=ConversationShellR1('s');shell.world=w('r',( ('x','y'),('y','z') ))
    r=ConversationalReasonerR1(shell).answer('Есть ли отношение r от x к z?',program_evidence=demos())
    assert r.task.admission.accepted and r.synthesis.selected is not None
    assert r.epistemic.state is EpistemicState.PROVED and r.surface.text=='Ответ: да.'
    assert r.surface.authoritative is False

def test_no_program_evidence_fails_closed_instead_of_guessing():
    shell=ConversationShellR1('s');shell.world=w('r',( ('x','y'),('y','z') ))
    r=ConversationalReasonerR1(shell).answer('Есть ли отношение r от x к z?',program_evidence=())
    assert r.epistemic.state is EpistemicState.UNRESOLVED and r.decision is None

def test_unparseable_task_fails_closed():
    shell=ConversationShellR1('s')
    r=ConversationalReasonerR1(shell).answer('Расскажи что-нибудь')
    assert r.task.task is None and r.epistemic.state is EpistemicState.UNRESOLVED

def test_target_answer_is_not_part_of_reasoner_api():
    import inspect
    sig=inspect.signature(ConversationalReasonerR1.answer)
    assert 'gold' not in sig.parameters and 'program' not in sig.parameters
