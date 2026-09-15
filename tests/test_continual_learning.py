from training.replay_buffer import ReplayBuffer, ReplayItem
from nexus_gllm.continual import PromotionGate, PromotionMetrics


def test_replay_sampling_preserves_protected_quota_and_is_deterministic():
    buf = ReplayBuffer()
    for i in range(20):
        buf.add(ReplayItem.create(task="old", payload={"i": i}, priority=1.0, protected=i < 5, generation="g1"))
    a = buf.sample(10, protected_quota=0.3, seed=17)
    b = buf.sample(10, protected_quota=0.3, seed=17)
    assert [x.id for x in a] == [x.id for x in b]
    assert sum(x.protected for x in a) >= 3


def test_promotion_gate_accepts_gain_without_regression():
    gate = PromotionGate(min_new_gain=0.02, max_legacy_drop=0.01)
    metrics = PromotionMetrics(
        baseline_new=0.70, candidate_new=0.75,
        baseline_legacy=0.90, candidate_legacy=0.895,
        protected_exact=1.0, invalid_mutation_rate=0.0,
    )
    decision = gate.decide(metrics)
    assert decision.promote is True


def test_promotion_gate_rejects_protected_regression():
    gate = PromotionGate(min_new_gain=0.02, max_legacy_drop=0.01)
    metrics = PromotionMetrics(
        baseline_new=0.70, candidate_new=0.80,
        baseline_legacy=0.90, candidate_legacy=0.89,
        protected_exact=0.99, invalid_mutation_rate=0.0,
    )
    decision = gate.decide(metrics)
    assert decision.promote is False
    assert "protected_exact" in decision.reasons
