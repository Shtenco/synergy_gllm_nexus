from __future__ import annotations

import argparse
import json
from pathlib import Path


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def belief_metrics(rows: list[dict]) -> dict:
    if not rows:
        return {"total": 0, "status_accuracy": 0.0, "brier_score": 0.0, "contradiction_precision": 0.0, "contradiction_recall": 0.0}
    status_accuracy = sum(bool(r.get("status_ok")) for r in rows) / len(rows)
    brier = sum((float(r["posterior"]) - float(r["expected"])) ** 2 for r in rows) / len(rows)
    tp = sum(bool(r.get("contradiction_expected")) and bool(r.get("contradiction_found")) for r in rows)
    fp = sum((not bool(r.get("contradiction_expected"))) and bool(r.get("contradiction_found")) for r in rows)
    fn = sum(bool(r.get("contradiction_expected")) and (not bool(r.get("contradiction_found"))) for r in rows)
    return {
        "total": len(rows),
        "status_accuracy": status_accuracy,
        "brier_score": brier,
        "contradiction_precision": _safe_div(tp, tp + fp),
        "contradiction_recall": _safe_div(tp, tp + fn),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="JSONL rows with posterior/expected/status/contradiction fields")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    result = belief_metrics(rows)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
