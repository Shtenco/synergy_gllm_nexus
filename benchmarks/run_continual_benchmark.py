from __future__ import annotations

import argparse
import json


def continual_metrics(*, baseline_new: float, candidate_new: float, baseline_legacy: float, candidate_legacy: float) -> dict:
    return {
        "baseline_new": baseline_new,
        "candidate_new": candidate_new,
        "new_task_gain": candidate_new - baseline_new,
        "baseline_legacy": baseline_legacy,
        "candidate_legacy": candidate_legacy,
        "legacy_retention": (candidate_legacy / baseline_legacy) if baseline_legacy else 0.0,
        "legacy_drop": baseline_legacy - candidate_legacy,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-new", type=float, required=True)
    parser.add_argument("--candidate-new", type=float, required=True)
    parser.add_argument("--baseline-legacy", type=float, required=True)
    parser.add_argument("--candidate-legacy", type=float, required=True)
    args = parser.parse_args()
    print(json.dumps(continual_metrics(
        baseline_new=args.baseline_new,
        candidate_new=args.candidate_new,
        baseline_legacy=args.baseline_legacy,
        candidate_legacy=args.candidate_legacy,
    ), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
