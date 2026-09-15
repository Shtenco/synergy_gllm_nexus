from nexus_gllm.continual import PromotionMetrics
from training.replay_buffer import ReplayBuffer, ReplayItem
from training.train_continual import evaluate_candidate, replay_mix


def test_replay_mix_contains_new_and_protected_old_items():
    buffer = ReplayBuffer()
    for i in range(8):
        buffer.add(ReplayItem.create(task="legacy", payload={"i": i}, priority=1.0, protected=i < 4, generation="g0"))
    new_items = [ReplayItem.create(task="new", payload={"i": i}, priority=2.0, protected=False, generation="g1") for i in range(4)]
    mixed = replay_mix(new_items, buffer, replay_count=4, protected_quota=0.5, seed=17)
    assert len(mixed) == 8
    assert sum(item.protected for item in mixed) >= 2
    assert sum(item.task == "new" for item in mixed) == 4


def test_candidate_evaluation_promotes_or_rolls_back_without_side_effects():
    good = PromotionMetrics(0.60, 0.66, 0.90, 0.895, 1.0, 0.0)
    report = evaluate_candidate(good, candidate_checkpoint="candidate.pt", rollback_checkpoint="base.pt", gradient_steps=120)
    assert report.decision.promote is True
    assert report.promoted_checkpoint == "candidate.pt"
    assert report.rollback_checkpoint == "base.pt"

    bad = PromotionMetrics(0.60, 0.70, 0.90, 0.85, 1.0, 0.0)
    rejected = evaluate_candidate(bad, candidate_checkpoint="candidate.pt", rollback_checkpoint="base.pt", gradient_steps=120)
    assert rejected.decision.promote is False
    assert rejected.promoted_checkpoint is None
