from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

from training.dataset import split_manifest


TEMPLATES = {
    "train": {
        "older_than": "{s} старше {o}.",
        "located_in": "{s} находится в {o}.",
        "owned_by": "{s} принадлежит {o}.",
        "before": "Сначала {s}, потом {o}.",
        "causes": "{s}, поэтому {o}.",
        "is_a": "{s} является {o}.",
        "world_revision": "Теперь {s} принадлежит {o}.",
        "abstain": "Опиши настроение {s}.",
    },
    "dev": {
        "older_than": "По возрасту {s} старше, чем {o}.",
        "located_in": "{s} расположен в {o}.",
        "owned_by": "Владельцем {s} является {o}.",
        "before": "{s} произошло раньше, чем {o}.",
        "causes": "Из-за того что {s}, произошло {o}.",
        "is_a": "{s} — это {o}.",
        "world_revision": "С этого момента {s} принадлежит {o}.",
        "abstain": "Нарисуй метафору про {s}.",
    },
    "blind": {
        "older_than": "Сравнение возраста: {s} старше {o}.",
        "located_in": "Местоположение объекта {s}: {o}.",
        "owned_by": "Объект {s} находится во владении {o}.",
        "before": "До события «{o}» случилось «{s}».",
        "causes": "Причиной события «{o}» стало «{s}».",
        "is_a": "Категория {s}: {o}.",
        "world_revision": "Новое состояние: {s} теперь принадлежит {o}.",
        "abstain": "Придумай стих о {s}.",
    },
}

RELATION_FOR_TASK = {
    "older_than": "older_than",
    "located_in": "located_in",
    "owned_by": "owned_by",
    "before": "before",
    "causes": "causes",
    "is_a": "is_a",
    "world_revision": "owned_by",
    "abstain": "abstain",
}

KIND_FOR_TASK = {
    "older_than": "statement",
    "located_in": "statement",
    "owned_by": "statement",
    "before": "temporal",
    "causes": "causal",
    "is_a": "statement",
    "world_revision": "statement",
    "abstain": "abstain",
}


def _template_hash(template: str) -> str:
    normalized = " ".join(template.casefold().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _entity(split: str, role: str, index: int) -> str:
    prefixes = {"train": "Трен", "dev": "Дев", "blind": "Блайнд"}
    return f"{prefixes[split]}{role}{index:05d}"


def _record(split: str, task: str, index: int) -> dict:
    template = TEMPLATES[split][task]
    subject = _entity(split, "Субъект", index)
    obj = _entity(split, "Объект", index)
    text = template.format(s=subject, o=obj)
    relation = RELATION_FOR_TASK[task]

    if relation == "abstain":
        target = {
            "kind": "abstain",
            "relation": "abstain",
            "subject_text": None,
            "object_text": None,
            "subject_span": None,
            "object_span": None,
            "confidence": 1.0,
        }
    else:
        s0 = text.index(subject)
        o0 = text.index(obj)
        target = {
            "kind": KIND_FOR_TASK[task],
            "relation": relation,
            "subject_text": subject,
            "object_text": obj,
            "subject_span": [s0, s0 + len(subject)],
            "object_span": [o0, o0 + len(obj)],
            "confidence": 1.0,
        }

    return {
        "id": f"{split}-compiler-{task}-{index:06d}",
        "input_text": text,
        "compiler_target": target,
        "task": f"compiler_{task}",
        "split": split,
        "template_hash": _template_hash(template),
        "provenance": "synthetic:omega1.1:compiler:v1",
    }


def _generate_split(rng: random.Random, split: str, count: int) -> list[dict]:
    tasks = list(TEMPLATES[split])
    rows: list[dict] = []
    offset = rng.randrange(0, len(tasks)) if tasks else 0
    for i in range(count):
        task = tasks[(i + offset) % len(tasks)]
        rows.append(_record(split, task, i))
    rng.shuffle(rows)
    return rows


def generate_compiler_records(
    seed: int = 17,
    train_count: int = 4000,
    dev_count: int = 800,
    blind_count: int = 800,
) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []
    rows.extend(_generate_split(rng, "train", train_count))
    rows.extend(_generate_split(rng, "dev", dev_count))
    rows.extend(_generate_split(rng, "blind", blind_count))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/omega1_1_compiler.jsonl"))
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--train", type=int, default=4000)
    parser.add_argument("--dev", type=int, default=800)
    parser.add_argument("--blind", type=int, default=800)
    args = parser.parse_args()

    rows = generate_compiler_records(args.seed, args.train, args.dev, args.blind)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "seed": args.seed,
        **split_manifest(rows),
        "template_hashes": {
            split: sorted({row["template_hash"] for row in rows if row["split"] == split})
            for split in ("train", "dev", "blind")
        },
    }
    manifest_path = args.out.with_suffix(args.out.suffix + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"path": str(args.out), "manifest": str(manifest_path), **manifest}, ensure_ascii=False))


if __name__ == "__main__":
    main()
