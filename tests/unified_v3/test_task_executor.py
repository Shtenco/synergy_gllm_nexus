import inspect, pytest
from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, WorldFact, WorldHypothesis, RuleProgram, RuleHypothesis, TaskOpcode, TaskProgram
from nexus_gllm.unified_v3.executor import Executor
from nexus_gllm.unified_v3.surface import SurfaceRequest
from nexus_gllm.unified_v3.task_induction import TaskExample, TaskInducer

def test_task_program_induced_without_task_name():
    ex=TaskExample(query_operator='op:q', expected_kind='relation_truth')
    assert TaskInducer().induce((ex,)).opcode is TaskOpcode.QUERY_RELATION

def test_three_hop_composition_has_provenance_depth_three():
    op=OperatorSymbol('op:q',2); E=Entity
    facts=tuple(WorldFact(op,(E(a),E(b))) for a,b in [('a','b'),('b','c'),('c','d')])
    world=WorldHypothesis('w1',facts)
    rules=RuleProgram((RuleHypothesis('r:transitive','transitive',1.0),))
    task=TaskProgram(TaskOpcode.QUERY_RELATION,operator_id='op:q',arguments=('a','d'))
    result=Executor().execute(world,rules,task,max_steps=5)
    assert result.truth is True and result.derivation is not None and result.derivation.depth==3

def test_executor_contract_is_text_free_and_rejects_surface_request():
    sig=inspect.signature(Executor.execute)
    assert all(p.name not in {'prompt','text','history'} for p in sig.parameters.values())
    with pytest.raises(TypeError): Executor().execute(SurfaceRequest('x'),RuleProgram(()),TaskProgram(TaskOpcode.QUERY_RELATION))

def test_five_step_bound_blocks_six_hop_proof():
    op=OperatorSymbol('op:q',2); E=Entity
    nodes=list('abcdefg')
    facts=tuple(WorldFact(op,(E(a),E(b))) for a,b in zip(nodes,nodes[1:]))
    world=WorldHypothesis('w',facts)
    rules=RuleProgram((RuleHypothesis('r','transitive',1.0),))
    task=TaskProgram(TaskOpcode.QUERY_RELATION,operator_id='op:q',arguments=('a','g'))
    assert Executor().execute(world,rules,task,max_steps=5).truth is None
