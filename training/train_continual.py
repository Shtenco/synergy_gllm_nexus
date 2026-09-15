from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from nexus_gllm.continual import ContinualLearningReport, PromotionGate, PromotionMetrics
from training.replay_buffer import ReplayBuffer, ReplayItem


def replay_mix(
    new_items: list[ReplayItem],
    replay_buffer: ReplayBuffer,
    *,
    replay_count: int,
    protected_quota: float = 0.25,
    seed: int = 17,
) -> tuple[ReplayItem, ...]:
    replay = replay_buffer.sample(replay_count, protected_quota=protected_quota, seed=seed)
    return tuple(new_items) + replay


def evaluate_candidate(
    metrics: PromotionMetrics,
    *,
    candidate_checkpoint: str | None,
    rollback_checkpoint: str | None,
    gradient_steps: int,
    min_new_gain: float = 0.02,
    max_legacy_drop: float = 0.01,
) -> ContinualLearningReport:
    gate = PromotionGate(min_new_gain=min_new_gain, max_legacy_drop=max_legacy_drop)
    decision = gate.decide(metrics)
    return ContinualLearningReport(
        decision=decision,
        metrics=metrics,
        candidate_checkpoint=candidate_checkpoint,
        promoted_checkpoint=candidate_checkpoint if decision.promote else None,
        rollback_checkpoint=rollback_checkpoint,
        gradient_steps=int(gradient_steps),
    )


def report_to_dict(report: ContinualLearningReport) -> dict:
    data = asdict(report)
    data["decision"] = {
        "promote": report.decision.promote,
        "reasons": list(report.decision.reasons),
    }
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Ω-1.2 continual-learning promotion/rollback gate runner")
    parser.add_argument("--baseline-new", type=float, required=True)
    parser.add_argument("--candidate-new", type=float, required=True)
    parser.add_argument("--baseline-legacy", type=float, required=True)
    parser.add_argument("--candidate-legacy", type=float, required=True)
    parser.add_argument("--protected-exact", type=float, required=True)
    parser.add_argument("--invalid-mutation-rate", type=float, required=True)
    parser.add_argument("--candidate-checkpoint")
    parser.add_argument("--rollback-checkpoint")
    parser.add_argument("--gradient-steps", type=int, default=0)
    parser.add_argument("--min-new-gain", type=float, default=0.02)
    parser.add_argument("--max-legacy-drop", type=float, default=0.01)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    metrics = PromotionMetrics(
        baseline_new=args.baseline_new,
        candidate_new=args.candidate_new,
        baseline_legacy=args.baseline_legacy,
        candidate_legacy=args.candidate_legacy,
        protected_exact=args.protected_exact,
        invalid_mutation_rate=args.invalid_mutation_rate,
    )
    report = evaluate_candidate(
        metrics,
        candidate_checkpoint=args.candidate_checkpoint,
        rollback_checkpoint=args.rollback_checkpoint,
        gradient_steps=args.gradient_steps,
        min_new_gain=args.min_new_gain,
        max_legacy_drop=args.max_legacy_drop,
    )
    data = report_to_dict(report)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
