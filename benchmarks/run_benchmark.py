from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from nexus_gllm.model import NexusGLLM
from training.dataset import GLLMDataset


def run(path: Path, split: str = "blind", core_checkpoint: Path | None = None) -> dict:
    ds = GLLMDataset(path, split=split)
    correct = 0
    rows = []
    per_task: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})

    for record in ds.rows:
        model = NexusGLLM()
        if core_checkpoint is not None:
            model.load_core_checkpoint(core_checkpoint)
        statements = record.get("statements")
        if statements is None:
            statements = [s.strip() for s in record["input_text"].split(".") if s.strip()]
        for sentence in statements:
            model.learn(sentence)
        response = model.ask(record["query_text"])
        ok = response.answer_graph.answer_value == record["answer"]
        correct += int(ok)
        task = record.get("task", "unknown")
        per_task[task]["total"] += 1
        per_task[task]["correct"] += int(ok)
        rows.append({
            "id": record["id"],
            "task": task,
            "expected": record["answer"],
            "predicted": response.answer_graph.answer_value,
            "text": response.text,
            "confidence": response.confidence,
            "cognition_logits": list(response.cognition_logits),
            "correct": ok,
        })

    total = len(rows)
    task_summary = {
        task: {
            **stats,
            "accuracy": stats["correct"] / stats["total"] if stats["total"] else 0.0,
        }
        for task, stats in sorted(per_task.items())
    }
    return {
        "split": split,
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
        "per_task": task_summary,
        "core_checkpoint": str(core_checkpoint) if core_checkpoint else None,
        "results": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--split", default="blind")
    parser.add_argument("--core-checkpoint", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run(args.data, args.split, args.core_checkpoint)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
