from nexus_gllm.unified_v3.cognitive.world_model import EmpiricalWorldModel
from nexus_gllm.unified_v3.cognitive.learned_planner import LearnedFuturePlanner
def train_model(envs,repeats=3):
    m=EmpiricalWorldModel()
    for e in envs:
        for _ in range(repeats):
            for t in e.transitions:m.observe(t.state,t.action,t.next_state,t.reward)
    return m
def first_action_accuracy(envs,depth):
    m=train_model(envs);correct=0
    for e in envs:
        p=LearnedFuturePlanner(m,max_depth=depth).plan(e.start);correct+=int(p.action==e.optimal_first)
    return correct/max(1,len(envs))
