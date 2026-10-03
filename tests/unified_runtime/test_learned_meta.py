from nexus_gllm.unified_runtime.types import CortexDecisionFeatures
from nexus_gllm.unified_runtime.learned_meta import LearnedMetaPolicy


def cf():
    return CortexDecisionFeatures(
        plan_probs=tuple([1/14]*14), relation_probs=(.5,.5), role_probs=tuple([1/8]*8), temporal_probs=(1/3,)*3,
        plan_entropy=1.0, relation_entropy=.69, role_entropy=2.0, temporal_entropy=1.0,
        uncertainty=.7, checkpoint_sha256='x', checkpoint_name='test', reconstruction_nhead=8,
        reconstruction_exact_source=False,
    )


def test_rpe_credit_update_changes_policy_hash():
    p=LearnedMetaPolicy(seed=7); c=cf(); d=p.decide(c,novelty=.8)
    before=p.parameter_hash(); tel=p.update(c,action_index=d.action_index,observed_reward=1.0,credit=.8,novelty=.8)
    after=p.parameter_hash()
    assert before!=after
    assert 'rpe' in tel and 'advantage' in tel


def test_frozen_evaluation_preserves_hash_and_blocks_update():
    p=LearnedMetaPolicy(seed=7); c=cf(); before=p.parameter_hash()
    with p.frozen_evaluation() as q:
        q.decide(c,novelty=.8)
        try:
            q.update(c,action_index=0,observed_reward=1.0,credit=1.0,novelty=.8)
        except RuntimeError as e:
            assert 'learning disabled' in str(e)
    assert p.parameter_hash()==before
