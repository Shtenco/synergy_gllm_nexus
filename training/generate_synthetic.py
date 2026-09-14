from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from training.dataset import split_manifest


def _split_names(prefix: str, count: int) -> list[str]:
    return [f"{prefix}{i:04d}" for i in range(count * 3 + 3)]


def _records_for_split(rng: random.Random, split: str, count: int, prefix: str) -> list[dict]:
    names = _split_names(prefix, count)
    rows: list[dict] = []
    for i in range(count):
        trio = names[i * 3 : i * 3 + 3]
        rng.shuffle(trio)
        a, b, c = trio
        rows.append({
            "id": f"{split}-transitive-{i:06d}",
            "input_text": f"{a} старше {b}. {b} старше {c}.",
            "query_text": "Кто самый старший?",
            "graphscript": (
                f'NODE a : PERSON ["{a}"]\n'
                f'NODE b : PERSON ["{b}"]\n'
                f'NODE c : PERSON ["{c}"]\n'
                "EDGE a -> b : older_than CONF=1.0\n"
                "EDGE b -> c : older_than CONF=1.0\n"
                "QUERY oldest(?)\nANSWER a"
            ),
            "answer": a,
            "entities": [a, b, c],
            "task": "transitive_reasoning",
            "split": split,
            "provenance": "synthetic:omega1:v1",
        })
    return rows


def generate_records(seed: int = 17, train_count: int = 1000, dev_count: int = 200, blind_count: int = 200) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []
    rows += _records_for_split(rng, "train", train_count, "Трен")
    rows += _records_for_split(rng, "dev", dev_count, "Дев")
    rows += _records_for_split(rng, "blind", blind_count, "Блайнд")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/omega1_synthetic.jsonl"))
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--train", type=int, default=1000)
    parser.add_argument("--dev", type=int, default=200)
    parser.add_argument("--blind", type=int, default=200)
    args = parser.parse_args()

    rows = generate_records(args.seed, args.train, args.dev, args.blind)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    manifest = split_manifest(rows)
    args.out.with_suffix(args.out.suffix + ".manifest.json").write_text(
        json.dumps({"seed": args.seed, **manifest}, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps({"path": str(args.out), **manifest}, ensure_ascii=False))


if __name__ == "__main__":
    main()
