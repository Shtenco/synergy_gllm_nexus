from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexus_gllm.model import NexusGLLM
from training.dataset import GLLMDataset


def run(path: Path, split: str = "blind") -> dict:
    ds = GLLMDataset(path, split=split)
    correct = 0
    rows = []
    for record in ds.rows:
        model = NexusGLLM()
        for sentence in [s.strip() for s in record["input_text"].split(".") if s.strip()]:
            model.learn(sentence)
        response = model.ask(record["query_text"])
        ok = response.answer_graph.answer_value == record["answer"]
        correct += int(ok)
        rows.append({
            "id": record["id"],
            "expected": record["answer"],
            "predicted": response.answer_graph.answer_value,
            "text": response.text,
            "confidence": response.confidence,
            "correct": ok,
        })
    total = len(rows)
    return {
        "split": split,
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
        "results": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--split", default="blind")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run(args.data, args.split)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
