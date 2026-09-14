from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from training.dataset import split_manifest


def _split_names(prefix: str, count: int) -> list[str]:
    return [f"{prefix}{i:04d}" for i in range(count * 4 + 8)]


def _transitive(split: str, i: int, a: str, b: str, c: str) -> dict:
    return {
        "id": f"{split}-transitive-{i:06d}",
        "statements": [f"{a} старше {b}", f"{b} старше {c}"],
        "input_text": f"{a} старше {b}. {b} старше {c}.",
        "query_text": "Кто самый старший?",
        "graphscript": (
            f'NODE a : PERSON ["{a}"]\nNODE b : PERSON ["{b}"]\nNODE c : PERSON ["{c}"]\n'
            "EDGE a -> b : older_than CONF=1.0\nEDGE b -> c : older_than CONF=1.0\n"
            "QUERY oldest(?)\nANSWER a"
        ),
        "answer": a,
        "entities": [a, b, c],
        "edge_index": [[0, 1], [1, 2]],
        "edge_types": [1, 1],
        "target_op": 5,
        "task": "transitive_reasoning",
        "split": split,
        "provenance": "synthetic:omega1:v2",
    }


def _location(split: str, i: int, obj: str, place: str) -> dict:
    return {
        "id": f"{split}-location-{i:06d}",
        "statements": [f"{obj} находится в {place}"],
        "input_text": f"{obj} находится в {place}.",
        "query_text": f"Где находится {obj}?",
        "answer": place,
        "entities": [obj, place],
        "edge_index": [[0, 1]],
        "edge_types": [2],
        "target_op": 5,
        "task": "location_lookup",
        "split": split,
        "provenance": "synthetic:omega1:v2",
    }


def _ownership(split: str, i: int, obj: str, owner: str) -> dict:
    return {
        "id": f"{split}-ownership-{i:06d}",
        "statements": [f"{obj} принадлежит {owner}"],
        "input_text": f"{obj} принадлежит {owner}.",
        "query_text": f"Кому принадлежит {obj}?",
        "answer": owner,
        "entities": [obj, owner],
        "edge_index": [[0, 1]],
        "edge_types": [3],
        "target_op": 5,
        "task": "ownership_lookup",
        "split": split,
        "provenance": "synthetic:omega1:v2",
    }


def _revision(split: str, i: int, obj: str, old_owner: str, new_owner: str) -> dict:
    return {
        "id": f"{split}-revision-{i:06d}",
        "statements": [f"{obj} принадлежит {old_owner}", f"{obj} принадлежит {new_owner}"],
        "input_text": f"{obj} принадлежит {old_owner}. Затем {obj} принадлежит {new_owner}.",
        "query_text": f"Кому принадлежит {obj}?",
        "answer": new_owner,
        "entities": [obj, old_owner, new_owner],
        "edge_index": [[0, 1], [0, 2]],
        "edge_types": [3, 4],
        "target_op": 4,
        "task": "world_revision",
        "split": split,
        "provenance": "synthetic:omega1:v2",
    }


def _records_for_split(rng: random.Random, split: str, count: int, prefix: str) -> list[dict]:
    names = _split_names(prefix, count)
    rows: list[dict] = []
    for i in range(count):
        base = i * 4
        a, b, c, d = names[base : base + 4]
        mode = i % 4
        if mode == 0:
            trio = [a, b, c]
            rng.shuffle(trio)
            rows.append(_transitive(split, i, *trio))
        elif mode == 1:
            rows.append(_location(split, i, f"Объект{a}", f"Место{b}"))
        elif mode == 2:
            rows.append(_ownership(split, i, f"Предмет{a}", b))
        else:
            rows.append(_revision(split, i, f"Предмет{a}", b, c))
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
        json.dumps({"seed": args.seed, "corpus_version": 2, **manifest}, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps({"path": str(args.out), **manifest}, ensure_ascii=False))


if __name__ == "__main__":
    main()
