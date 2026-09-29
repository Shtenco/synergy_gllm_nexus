from nexus_gllm.unified_v3.cognitive.credit import CognitiveTraceGraph
from nexus_gllm.unified_v3.cognitive.credit_learning import RecursiveCreditLearner
from nexus_gllm.unified_v3.cognitive.runtime import CognitiveRecursiveCoreR1
from nexus_gllm.unified_v3.cognitive.state import NexusCognitiveState
from nexus_gllm.unified_v3.cognitive.reward import RewardVector
def graph():
    g=CognitiveTraceGraph()
    g.add_node('router','router',{'capability':'routing'});g.add_node('good','expert',{'capability':'good_expert'});g.add_node('bad','expert',{'capability':'bad_expert'});g.add_node('answer','answer');g.add_node('out','outcome')
    g.connect('router','good',1);g.connect('router','bad',1);g.connect('good','answer',.5);g.connect('bad','answer',.5);g.connect('answer','out',1);return g
def test_counterfactual_credit_separates_correlated_contributors():
    l=RecursiveCreditLearner(blend=.8);g=graph()
    for _ in range(12):l.update(g,'out',1.0,counterfactual_credit={'good':.9,'bad':-.7,'router':.2})
    assert l.trust('good')>l.trust('router')>l.trust('bad')
def test_negative_credit_updates_self_model_reliability():
    l=RecursiveCreditLearner(blend=1.0);g=graph();l.update(g,'out',-1,counterfactual_credit={'good':.4,'bad':-.9,'router':-.2})
    assert l.self_model.get('good_expert').reliability>l.self_model.get('bad_expert').reliability
def test_crc_close_episode_persists_credit_learning():
    core=CognitiveRecursiveCoreR1();g=graph();s=NexusCognitiveState('e',predicted_reward=.1)
    core.close_episode(s,answer='x',reward=RewardVector(task=1),trace_graph=g,outcome_node_id='out',counterfactual_credit={'good':.8,'bad':-.5})
    assert core.credit_learner.get('good').count==1 and core.credit_learner.trust('good')>core.credit_learner.trust('bad')
