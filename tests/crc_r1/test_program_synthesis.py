from nexus_gllm.unified_v3.cognitive.program_synthesis import *
from nexus_gllm.unified_v3.contracts import *
from nexus_gllm.unified_v3.cognitive.higher_order import HigherOrderContext,HigherOrderExecutor
def w(op,edges):
    o=OperatorSymbol(op,2);return WorldHypothesis(op,tuple(WorldFact(o,(Entity(a),Entity(b)),True) for a,b in edges))
def test_evidence_selects_transitive_structure_without_target_gold():
    demos=(
      ProgramEvidenceCase(w('r',( ('a','b'),('b','c') )),TaskProgram(TaskOpcode.QUERY_RELATION,'r',('a','c')),True),
      ProgramEvidenceCase(w('r',( ('d','e'),('e','f') )),TaskProgram(TaskOpcode.QUERY_RELATION,'r',('d','f')),True),
    )
    target=w('r',( ('x','y'),('y','z') ));task=TaskProgram(TaskOpcode.QUERY_RELATION,'r',('x','z'))
    s=ProgramSynthesisCortex().synthesize(target,task,demos)
    assert s.selected is not None and 'transitive:r' in str(s.selected.canonical())
    assert HigherOrderExecutor().execute(s.selected,HigherOrderContext(target,task)).execution.truth is True
def test_no_evidence_means_no_selected_program():
    target=w('r',( ('a','b'), ));task=TaskProgram(TaskOpcode.QUERY_RELATION,'r',('a','b'))
    assert ProgramSynthesisCortex().synthesize(target,task,()).selected is None
def test_complexity_penalty_prefers_simple_equally_fitting_program():
    e=(ProgramEvidenceCase(w('r',( ('a','b'),('b','c') )),TaskProgram(TaskOpcode.QUERY_RELATION,'r',('a','c')),True),)
    c=ProgramSynthesisCortex();simple=ProgramNode(ProgramKind.ATOM,'rule:transitive:r');complexp=ProgramNode(ProgramKind.SEQUENCE,children=(simple,simple))
    assert c.score(simple,e).total_score>c.score(complexp,e).total_score
