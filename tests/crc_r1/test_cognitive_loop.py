from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1,CognitiveRequest
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind,ProgramNode
from nexus_gllm.unified_v3.cognitive.reward import RewardVector
from nexus_gllm.unified_v3.cognitive.world_model import EmpiricalWorldModel
from nexus_gllm.unified_v3.contracts import Entity,OperatorSymbol,TaskOpcode,TaskProgram,WorldFact,WorldHypothesis

def request(**kw):
    op=OperatorSymbol('r',2)
    w=WorldHypothesis('w',(WorldFact(op,(Entity('a'),Entity('b'))),WorldFact(op,(Entity('b'),Entity('c')))))
    t=TaskProgram(TaskOpcode.QUERY_RELATION,'r',('a','c'))
    p=ProgramNode(ProgramKind.ATOM,'rule:transitive:r')
    base=dict(episode_id='ep',world=w,task=t,program=p,novelty=.8,uncertainty=.7,memory_tags=('topic',),planning_state='s')
    base.update(kw);return CognitiveRequest(**base)

def test_loop_integrates_memory_program_plan_and_trace():
    wm=EmpiricalWorldModel();wm.observe('s','safe','done',.5);wm.observe('s','invest','mid',-.1);wm.observe('mid','continue','goal',2.0)
    loop=CognitiveLoopR1(world_model=wm);loop.core.memory.add_raw({'x':1},tags=('topic',));loop.core.memory.add_raw({'x':2},tags=('topic',))
    d=loop.deliberate(request())
    assert d.execution.execution.truth is True and d.memories and d.plan is not None
    program='program:'+d.state.program_ids[0]
    memory_nodes=[n.node_id for n in d.trace_graph.nodes.values() if n.kind=='memory']
    assert len(memory_nodes)==2
    assert all(any(e.parent_id==m and e.child_id==program for e in d.trace_graph.edges) for m in memory_nodes)
    assert not any(e.parent_id in memory_nodes and e.child_id in memory_nodes for e in d.trace_graph.edges)

def test_planning_value_does_not_overwrite_episode_reward_prediction():
    wm=EmpiricalWorldModel();wm.observe('s','a','x',5.0)
    d=CognitiveLoopR1(world_model=wm).deliberate(request(memory_tags=(),predicted_outcome_reward=.25))
    assert d.plan is not None and d.plan.value!=.25 and d.state.predicted_reward==.25

def test_observation_updates_recursive_credit_and_self_model():
    loop=CognitiveLoopR1();r=request(novelty=.2,uncertainty=.2,memory_tags=(),planning_state=None,predicted_outcome_reward=.1)
    d=loop.deliberate(r);out=loop.observe(d,RewardVector(task=1.0),counterfactual_credit={'program:'+r.program.program_id:.8,'meta':.1})
    assert abs(out.rpe-.9)<1e-12
    assert loop.core.credit_learner.get('program:'+r.program.program_id).count==1
    assert loop.core.self_model.get('program_execution').credit_mass>0

def test_deliberation_does_not_mutate_world():
    r=request(memory_tags=(),planning_state=None);before=r.world.facts;CognitiveLoopR1().deliberate(r);assert r.world.facts==before
