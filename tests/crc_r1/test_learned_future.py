from nexus_gllm.unified_v3.cognitive.world_model import EmpiricalWorldModel
from nexus_gllm.unified_v3.cognitive.learned_planner import LearnedFuturePlanner
from benchmarks.future_m5.generator import generate
from benchmarks.future_m5.runner import train_model,first_action_accuracy
def test_world_model_learns_transition_and_reward():
    m=EmpiricalWorldModel();m.observe('s','a','n',.5);m.observe('s','a','n',1.0);p=m.predict('s','a');assert p.next_state=='n' and abs(p.expected_reward-.75)<1e-9 and p.count==2
def test_unknown_action_is_uncertain():
    p=EmpiricalWorldModel().predict('s','a');assert p.uncertainty==1.0 and p.count==0
def test_depth_three_finds_delayed_reward_better_than_depth_one():
    envs=generate(seed=3,n=40);a1=first_action_accuracy(envs,1);a3=first_action_accuracy(envs,3);assert a3>a1 and a3>.9
def test_edge_reward_is_attributed_to_parent_transition():
    m=EmpiricalWorldModel();m.observe('root','invest','middle',-.1);m.observe('middle','continue','goal',2.0);m.observe('root','safe','done',.6)
    assert LearnedFuturePlanner(m,max_depth=1).plan('root').action=='safe'
    assert LearnedFuturePlanner(m,max_depth=2).plan('root').action=='invest'
