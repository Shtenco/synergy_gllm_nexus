from __future__ import annotations

import argparse
import json


def forgetting_metrics(*, before: float, after: float, protected_before: float, protected_after: float) -> dict:
    return {
        "before": before,
        "after": after,
        "forgetting_delta": before - after,
        "retention": (after / before) if before else 0.0,
        "protected_before": protected_before,
        "protected_after": protected_after,
        "protected_exact_retention": (protected_after / protected_before) if protected_before else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=float, required=True)
    parser.add_argument("--after", type=float, required=True)
    parser.add_argument("--protected-before", type=float, required=True)
    parser.add_argument("--protected-after", type=float, required=True)
    args = parser.parse_args()
    print(json.dumps(forgetting_metrics(
        before=args.before,
        after=args.after,
        protected_before=args.protected_before,
        protected_after=args.protected_after,
    ), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
