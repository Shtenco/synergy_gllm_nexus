from nexus_gllm.unified_v3.contracts import *
from nexus_gllm.unified_v3.executor import Executor
from nexus_gllm.unified_v3.rule_algebra import RuleClause
from nexus_gllm.unified_v3.task_induction import TaskExample, TaskInducer
def test_rich_task_opcodes_are_inducible():
    assert TaskInducer().induce((TaskExample('op:q','minimal_proof'),)).opcode is TaskOpcode.FIND_MINIMAL_PROOF
    assert TaskInducer().induce((TaskExample('op:q','current_state'),)).opcode is TaskOpcode.CURRENT_STATE
def test_symmetric_rule_executes():
    op=OperatorSymbol('op:q',2); w=WorldHypothesis('w',(WorldFact(op,(Entity('a'),Entity('b'))),))
    out=Executor().execute(w,RuleProgram(clauses=(RuleClause.symmetric('op:q'),)),TaskProgram(TaskOpcode.QUERY_RELATION,'op:q',('b','a')))
    assert out.truth is True
