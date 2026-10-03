from nexus_gllm.unified_runtime.crc_bridge import CRCOrganBridge
from nexus_gllm.unified_runtime.types import CortexDecisionFeatures, LearnedMetaDecision


def cortex(uncertainty=.35):
    return CortexDecisionFeatures(
        plan_probs=tuple([1/14]*14),
        relation_probs=(.6,.4),
        role_probs=tuple([1/8]*8),
        temporal_probs=(.5,.3,.2),
        plan_entropy=2.0,
        relation_entropy=.67,
        role_entropy=2.0,
        temporal_entropy=1.0,
        uncertainty=uncertainty,
        checkpoint_sha256='synthetic-contract',
        checkpoint_name='contract-test',
        reconstruction_nhead=8,
        reconstruction_exact_source=False,
    )


def meta():
    probs=[.01]*27
    probs[5]=.50; probs[7]=.25; probs[2]=.05
    total=sum(probs); probs=[x/total for x in probs]
    return LearnedMetaDecision(
        expert_top_k=3,
        branch_depth=2,
        branch_fanout=3,
        memory_limit=8,
        verification_level=2,
        action_index=5,
        action_probs=tuple(probs),
        value_estimate=.1,
        uncertainty=.35,
    )


def test_crc_bridge_records_memory_future_tree_and_positive_recursive_credit():
    bridge=CRCOrganBridge()
    ep=bridge.record_decision(
        episode_id='ep1', text='Запомни факт.', session_id='s1', dialogue_intent='memory_store',
        cortex=cortex(), meta=meta(), novelty=.4,
    )
    assert ep.memory_id.startswith('mem:')
    assert ep.best_branch_id is not None and ep.best_branch_id.startswith('root/')
    assert bridge.memory.get(ep.memory_id).raw_provenance==(ep.memory_id,)

    out=bridge.close_episode(ep,task_reward=1.0,progress=.2)
    assert out.rpe>0
    assert out.meta_credit>0
    assert out.credit['learned_meta']>0
    assert bridge.self_model.get('learned_meta_policy').credit_mass>0
    assert out.state.observed_reward is not None


def test_crc_bridge_counterfactual_negative_credit_changes_attribution_sign():
    bridge=CRCOrganBridge()
    ep=bridge.record_decision(
        episode_id='ep2', text='Почему сбой?', session_id='s2', dialogue_intent='causal_query',
        cortex=cortex(.8), meta=meta(), novelty=.9,
    )
    assert 'causal' in ep.graph.nodes
    out=bridge.close_episode(
        ep,
        task_reward=-.5,
        contradiction=.4,
        counterfactual_credit={'learned_meta':-.75},
    )
    assert out.rpe<0
    assert out.meta_credit<0
    assert bridge.self_model.get('learned_meta_policy').credit_mass<0
