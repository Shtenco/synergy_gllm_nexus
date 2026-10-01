from nexus_gllm.unified_v3.cognitive import *
from nexus_gllm.unified_v3.cognitive.runtime import CognitiveRecursiveCoreR1
from nexus_gllm.unified_v3.cognitive.reward import RewardVector
def test_memory_consolidation_never_loses_raw_provenance():
    m=HierarchicalMemoryStore();a=m.add_raw({'obs':'A'},tags=('x',));b=m.add_raw({'obs':'B'},tags=('x',));ep=m.consolidate(MemoryLevel.EPISODIC,{'episode':1},(a.memory_id,b.memory_id));sem=m.consolidate(MemoryLevel.SEMANTIC,{'fact':'A+B'},(ep.memory_id,));meta=m.consolidate(MemoryLevel.META,{'rule':'combine'},(sem.memory_id,));assert set(meta.raw_provenance)=={a.memory_id,b.memory_id};assert m.audit_provenance()==()
def test_program_synthesizer_creates_unseen_compositions():
    s=ProgramSynthesizer();out=s.expand(s.atoms(('A','B')),max_depth=3,max_candidates=40);assert any(n.kind is ProgramKind.COUNTERFACTUAL for n in out);assert any(n.kind is ProgramKind.INHIBIT and n.depth>1 for n in out)
def test_future_tree_values_information_and_causal_consistency():
    p=FutureTreePlanner(max_depth=1,fanout=3,beam_width=3,weights=(1,.8,.8,.4,.1,.2))
    def expand(_):return [('safe',1,'safe'),('curious',2,'curious')]
    def evaluate(state,action,depth):return BranchValue(expected_reward=.8,causal_consistency=.1,uncertainty=.1) if action=='safe' else BranchValue(expected_reward=.55,information_gain=.8,causal_consistency=.8,uncertainty=.15)
    assert p.best(p.plan(0,expand,evaluate)).action=='curious'
def test_rpe_and_recursive_credit_propagate_to_router_and_memory():
    g=CognitiveTraceGraph()
    for nid,kind in [('router','router'),('expert','expert'),('memory','memory'),('branch','branch'),('answer','answer'),('outcome','outcome')]:g.add_node(nid,kind)
    g.connect('router','expert',1).connect('memory','branch',1).connect('expert','answer',.7).connect('branch','answer',.3).connect('answer','outcome',1);c=g.propagate('outcome',1,decay=.9);assert c['router']>0 and c['memory']>0 and c['expert']>c['branch']
def test_self_model_and_meta_controller_allocate_more_compute_for_novelty():
    sm=NexusSelfModel();sm.observe('graph',success=True,credit=.5);b=sm.observe('graph',success=False,credit=-.2);assert 0<b.reliability<1;mc=MetaController();budget=ComputeBudget(1,3,4,4,16);easy=mc.decide(novelty=.1,uncertainty=.1,budget=budget,self_model=sm);hard=mc.decide(novelty=.9,uncertainty=.8,budget=budget,self_model=sm);assert hard.branch_depth>=easy.branch_depth and hard.expert_top_k>=easy.expert_top_k
def test_slow_learning_fails_closed_without_promotion_evidence():
    p=ContinualLearningPolicy();assert p.allow('raw_memory') and not p.allow('core_weights');assert p.allow('core_weights',PromotionEvidence(True,0,.01,True,True));assert not p.allow('core_weights',PromotionEvidence(True,-.01,0,True,True))
def test_cognitive_state_is_immutable_and_trace_is_append_only():
    s=NexusCognitiveState('ep1',predicted_reward=.2);s2=s.transition('plan',ref_id='p1',novelty=.7);assert s.step==0 and s.trace==() and s2.step==1 and s2.novelty==.7
def test_crc_close_episode_computes_rpe_and_credit():
    core=CognitiveRecursiveCoreR1();s=NexusCognitiveState('ep1',predicted_reward=.2);g=CognitiveTraceGraph();g.add_node('router','router');g.add_node('outcome','outcome');g.connect('router','outcome',1);out=core.close_episode(s,answer='A',reward=RewardVector(task=1),trace_graph=g,outcome_node_id='outcome');assert out.reward==1 and abs(out.rpe-.8)<1e-9 and out.credit['router']>0
