from nexus_gllm.unified_v3.cognitive.credit import CognitiveTraceGraph
from nexus_gllm.unified_v3.cognitive.credit_learning import RecursiveCreditLearner
def run(episodes=200):
    g=CognitiveTraceGraph();g.add_node('router','router');g.add_node('causal','expert');g.add_node('spurious','expert');g.add_node('answer','answer');g.add_node('out','outcome');g.connect('router','causal',1);g.connect('router','spurious',1);g.connect('causal','answer',.5);g.connect('spurious','answer',.5);g.connect('answer','out',1)
    learner=RecursiveCreditLearner(blend=.8)
    for i in range(episodes):
        good=(i%5)!=0;rpe=1.0 if good else -1.0
        cf={'causal':.9 if good else -.6,'spurious':-.5 if good else .2,'router':.15 if good else -.15}
        learner.update(g,'out',rpe,counterfactual_credit=cf)
    return {'causal_trust':learner.trust('causal'),'spurious_trust':learner.trust('spurious'),'router_trust':learner.trust('router'),'causal_mean_credit':learner.get('causal').mean_credit,'spurious_mean_credit':learner.get('spurious').mean_credit}
