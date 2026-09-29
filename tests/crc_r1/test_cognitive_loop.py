from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1,CognitiveRequest
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind,ProgramNode
from nexus_gllm.unified_v3.cognitive.reward import RewardVector
from nexus_gllm.unified_v3.cognitive.world_model import EmpiricalWorldModel
from nexus_gllm.unified_v3.contracts import Entity,OperatorSymbol,TaskOpcode,TaskProgram,WorldFact,WorldHypothesis

def request():
    op=OperatorSymbol('r',2)
    w=WorldHypothesis('w',(WorldFact(op,(Entity('a'),Entity('b'))),WorldFact(op,(Entity('b'),Entity('c')))))
    t=TaskProgram(TaskOpcode.QUERY_RELATION,'r',('a','c'))
    p=ProgramNode(ProgramKind.ATOM,'rule:transitive:r')
    return CognitiveRequest('ep',w,t,p,novelty=.8,uncertainty=.7,memory_tags=('topic',),planning_state='s')

def test_loop_integrates_memory_program_plan_and_trace():
    wm=EmpiricalWorldModel();wm.observe('s','safe','done',.5);wm.observe('s','invest','mid',-.1);wm.observe('mid','continue','goal',2.0)
    loop=CognitiveLoopR1(world_model=wm);loop.core.memory.add_raw({'x':1},tags=('topic',))
    d=loop.deliberate(request())
    assert d.execution.execution.truth is True
    assert d.memories and d.plan is not None
    assert any(n.kind=='memory' for n in d.trace_graph.nodes.values())
    assert any(n.kind=='program' for n in d.trace_graph.nodes.values())
    assert any(n.kind=='branch' for n in d.trace_graph.nodes.values())

def test_observation_updates_recursive_credit_and_self_model():
    loop=CognitiveLoopR1();r=request();r=CognitiveRequest(r.episode_id,r.world,r.task,r.program,novelty=.2,uncertainty=.2)
    d=loop.deliberate(r);out=loop.observe(d,RewardVector(task=1.0),counterfactual_credit={'program:'+r.program.program_id:.8,'meta':.1})
    assert out.reward==1.0
    assert loop.core.credit_learner.get('program:'+r.program.program_id).count==1
    assert loop.core.self_model.get('program_execution').credit_mass>0

def test_deliberation_does_not_mutate_world():
    r=request();before=r.world.facts;CognitiveLoopR1().deliberate(CognitiveRequest(r.episode_id,r.world,r.task,r.program,novelty=.1,uncertainty=.1));assert r.world.facts==before
