from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path


TASK_WEIGHTS = {
    "ordinary_relation": 20000,
    "contradictory_evidence": 15000,
    "source_reliability": 10000,
    "temporal_revision": 10000,
    "causal_evidence": 10000,
    "multi_source_agreement": 10000,
    "continual_memory_retention": 10000,
    "misinformation_correction": 5000,
    "abstention_unknown": 5000,
    "protected_facts_rollback": 5000,
}
TOTAL_WEIGHT = sum(TASK_WEIGHTS.values())

SPLIT_PREFIX = {
    "train": ("tr", "trsrc", "TR"),
    "dev": ("dev", "devsrc", "DV"),
    "blind": ("bl", "blsrc", "BL"),
}

RELATION_SURFACES = {
    "train": {
        "owned_by": "{s} принадлежит {o}",
        "located_in": "{s} находится в {o}",
        "is_a": "{s} является {o}",
        "older_than": "{s} старше {o}",
    },
    "dev": {
        "owned_by": "Владельцем {s} является {o}",
        "located_in": "{s} расположен в {o}",
        "is_a": "{s} относится к классу {o}",
        "older_than": "{s} по возрасту старше, чем {o}",
    },
    "blind": {
        "owned_by": "{o} владеет объектом {s}",
        "located_in": "Местонахождение {s} — {o}",
        "is_a": "К категории {o} относится {s}",
        "older_than": "По сравнению с {o}, {s} старше",
    },
}

TEMPORAL_SURFACE = {
    "train": "Сначала {a}, потом {b}.",
    "dev": "После того как {a}, произошло {b}.",
    "blind": "{b} случилось вслед за тем, как {a}.",
}

CAUSAL_SURFACE = {
    "train": "{a}, поэтому {b}.",
    "dev": "{b} произошло вследствие того, что {a}.",
    "blind": "Причиной того, что {b}, стало событие: {a}.",
}

ABSTAIN_SURFACE = {
    "train": "Возможно, {s} связан с {o}, но данных недостаточно",
    "dev": "Нет достаточных оснований утверждать связь между {s} и {o}",
    "blind": "Сведения о связи {s} с {o} противоречивы и недостаточны",
}


def _allocation(total: int) -> dict[str, int]:
    raw = {task: total * weight / TOTAL_WEIGHT for task, weight in TASK_WEIGHTS.items()}
    base = {task: int(value) for task, value in raw.items()}
    remainder = total - sum(base.values())
    ranked = sorted(TASK_WEIGHTS, key=lambda task: (-(raw[task] - base[task]), task))
    for task in ranked[:remainder]:
        base[task] += 1
    return base


def _relation_text(split: str, relation: str, subject: str, obj: str) -> tuple[str, str]:
    surface = RELATION_SURFACES[split][relation]
    return surface.format(s=subject, o=obj), surface


def _template(split: str, task: str, surface_template: str) -> tuple[str, str]:
    _, _, code = SPLIT_PREFIX[split]
    template_id = f"{code}:{task}:{hashlib.sha256(surface_template.encode('utf-8')).hexdigest()[:10]}"
    return template_id, hashlib.sha256(surface_template.encode("utf-8")).hexdigest()[:16]


def _obs(text: str, source: str, confidence: float, seq: int, polarity: str = "support") -> dict:
    return {
        "text": text,
        "source": source,
        "confidence": round(float(confidence), 4),
        "polarity": polarity,
        "sequence_index": seq,
    }


def _row(split: str, task: str, i: int, rng: random.Random) -> dict:
    entity_prefix, source_prefix, _ = SPLIT_PREFIX[split]
    subject = f"{entity_prefix}_объект_{i:06d}"
    obj_a = f"{entity_prefix}_A_{i:06d}"
    obj_b = f"{entity_prefix}_B_{i:06d}"
    source_a = f"{source_prefix}-{i:06d}-a"
    source_b = f"{source_prefix}-{i:06d}-b"
    source_c = f"{source_prefix}-{i:06d}-c"
    observations: list[dict] = []
    relation = "owned_by"
    expected = {"status": "active", "object": obj_a, "gradient_steps": 0}
    protected = False
    order_pattern = "single"
    surface_template = ""

    if task == "ordinary_relation":
        relation = ("owned_by", "located_in", "is_a", "older_than")[i % 4]
        text, surface_template = _relation_text(split, relation, subject, obj_a)
        observations = [_obs(text, source_a, 0.95, 1)]

    elif task == "contradictory_evidence":
        relation = "owned_by"
        text_a, surface_template = _relation_text(split, relation, subject, obj_a)
        text_b, _ = _relation_text(split, relation, subject, obj_b)
        observations = [_obs(text_a, source_a, 0.72, 1), _obs(text_b, source_b, 0.98, 2)]
        expected = {"status": "disputed", "object": obj_b, "gradient_steps": 0, "contradiction": True}
        order_pattern = "weak_then_strong_conflict"

    elif task == "source_reliability":
        relation = "owned_by"
        text_a, surface_template = _relation_text(split, relation, subject, obj_a)
        text_b, _ = _relation_text(split, relation, subject, obj_b)
        observations = [
            _obs(text_a, source_a, 0.90, 1),
            _obs(text_a, source_a, 0.90, 2),
            _obs(text_b, source_b, 0.90, 3),
        ]
        expected = {
            "status": "active",
            "object": obj_a,
            "gradient_steps": 0,
            "source_feedback": [
                {"source": source_a, "was_correct": True, "weight": 3.0},
                {"source": source_b, "was_correct": False, "weight": 2.0},
            ],
        }
        order_pattern = "reliable_repeat_vs_unreliable_conflict"

    elif task == "temporal_revision":
        relation = "before"
        event_a = f"{subject} начался"
        event_b = f"{obj_a} завершился"
        surface_template = TEMPORAL_SURFACE[split]
        observations = [_obs(surface_template.format(a=event_a, b=event_b), source_a, 0.95, 1)]
        expected = {"status": "active", "before": [event_a, event_b], "gradient_steps": 0}
        order_pattern = "temporal_sequence"

    elif task == "causal_evidence":
        relation = "causes"
        cause = f"{subject} усилился"
        effect = f"{obj_a} произошло"
        surface_template = CAUSAL_SURFACE[split]
        observations = [_obs(surface_template.format(a=cause, b=effect), source_a, 0.95, 1)]
        expected = {"status": "active", "cause": cause, "effect": effect, "gradient_steps": 0}
        order_pattern = "cause_then_effect"

    elif task == "multi_source_agreement":
        relation = "owned_by"
        text_a, surface_template = _relation_text(split, relation, subject, obj_a)
        observations = [
            _obs(text_a, source_a, 0.78, 1),
            _obs(text_a, source_b, 0.82, 2),
            _obs(text_a, source_c, 0.88, 3),
        ]
        expected = {"status": "active", "object": obj_a, "gradient_steps": 0, "agreement": 3}
        order_pattern = "three_source_agreement"

    elif task == "continual_memory_retention":
        relation = "located_in"
        text_a, surface_template = _relation_text(split, relation, subject, obj_a)
        observations = [_obs(text_a, source_a, 0.97, 1)]
        expected = {"status": "active", "object": obj_a, "gradient_steps": 0, "retain_after_sleep": True}
        order_pattern = "learn_then_sleep_retain"

    elif task == "misinformation_correction":
        relation = "located_in"
        text_b, surface_template = _relation_text(split, relation, subject, obj_b)
        text_a, _ = _relation_text(split, relation, subject, obj_a)
        observations = [_obs(text_b, source_a, 0.68, 1), _obs(text_a, source_b, 0.99, 2)]
        expected = {"status": "disputed", "object": obj_a, "gradient_steps": 0, "correction": True}
        order_pattern = "misinformation_then_correction"

    elif task == "abstention_unknown":
        relation = "unknown"
        surface_template = ABSTAIN_SURFACE[split]
        observations = [_obs(surface_template.format(s=subject, o=obj_a), source_a, 0.20, 1)]
        expected = {"status": "unknown", "object": None, "gradient_steps": 0, "abstain": True}
        order_pattern = "uncertain_observation"

    elif task == "protected_facts_rollback":
        relation = "is_a"
        text_a, surface_template = _relation_text(split, relation, subject, obj_a)
        observations = [_obs(text_a, source_a, 1.0, 1)]
        expected = {"status": "active", "object": obj_a, "gradient_steps": 0, "protected_exact": 1.0}
        protected = True
        order_pattern = "protected_then_candidate_update"

    else:
        raise ValueError(f"unknown task: {task}")

    template_id, template_hash = _template(split, task, surface_template)
    return {
        "id": f"{split}-{task}-{i:06d}",
        "split": split,
        "task": task,
        "relation": relation,
        "subject": subject,
        "object": obj_a,
        "alternate_object": obj_b,
        "observations": observations,
        "expected": expected,
        "protected": protected,
        "template_id": template_id,
        "template_hash": template_hash,
        "surface_template": surface_template,
        "order_pattern": order_pattern,
        "provenance": "synthetic:omega1.2:stage-a",
    }


def _split_rows(split: str, total: int, rng: random.Random) -> list[dict]:
    allocation = _allocation(total)
    rows: list[dict] = []
    for task in TASK_WEIGHTS:
        for i in range(allocation[task]):
            rows.append(_row(split, task, i, rng))
    rng.shuffle(rows)
    return rows


def generate_records(
    *,
    seed: int = 17,
    train_total: int = 100000,
    dev_total: int = 10000,
    blind_total: int = 10000,
) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []
    rows.extend(_split_rows("train", train_total, rng))
    rows.extend(_split_rows("dev", dev_total, rng))
    rows.extend(_split_rows("blind", blind_total, rng))
    return rows


def build_manifest(rows: list[dict], *, seed: int) -> dict:
    counts = Counter(row["split"] for row in rows)
    task_counts: dict[str, dict[str, int]] = {}
    template_hashes: dict[str, list[str]] = {}
    surface_hashes: dict[str, list[str]] = {}
    for split in ("train", "dev", "blind"):
        split_rows = [row for row in rows if row["split"] == split]
        task_counts[split] = dict(sorted(Counter(row["task"] for row in split_rows).items()))
        template_hashes[split] = sorted({row["template_hash"] for row in split_rows})
        surface_hashes[split] = sorted({hashlib.sha256(row["surface_template"].encode("utf-8")).hexdigest() for row in split_rows})
    canonical = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for row in rows)
    return {
        "version": "omega1.2-stage-a-surface-disjoint",
        "seed": seed,
        "counts": {name: counts.get(name, 0) for name in ("train", "dev", "blind")},
        "task_counts": task_counts,
        "template_hashes": template_hashes,
        "surface_hashes": surface_hashes,
        "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_corpus(path: Path, rows: list[dict], *, seed: int) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    manifest = build_manifest(rows, seed=seed)
    manifest_path = path.with_suffix(path.suffix + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/omega1_2_belief_100k.jsonl"))
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--train", type=int, default=100000)
    parser.add_argument("--dev", type=int, default=10000)
    parser.add_argument("--blind", type=int, default=10000)
    args = parser.parse_args()
    rows = generate_records(seed=args.seed, train_total=args.train, dev_total=args.dev, blind_total=args.blind)
    manifest = write_corpus(args.out, rows, seed=args.seed)
    print(json.dumps({"path": str(args.out), **manifest}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
