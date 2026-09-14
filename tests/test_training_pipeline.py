import json
from pathlib import Path

from training.generate_synthetic import generate_records
from training.dataset import GLLMDataset, split_manifest


def test_synthetic_generation_is_seed_deterministic_and_split_disjoint(tmp_path: Path):
    a = generate_records(seed=17, train_count=12, dev_count=4, blind_count=4)
    b = generate_records(seed=17, train_count=12, dev_count=4, blind_count=4)
    assert a == b

    by_split = {name: [r for r in a if r["split"] == name] for name in ("train", "dev", "blind")}
    entity_sets = {
        name: {e for row in rows for e in row["entities"]}
        for name, rows in by_split.items()
    }
    assert entity_sets["train"].isdisjoint(entity_sets["blind"])
    assert entity_sets["dev"].isdisjoint(entity_sets["blind"])

    path = tmp_path / "data.jsonl"
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in a), encoding="utf-8")
    ds = GLLMDataset(path, split="train")
    assert len(ds) == 12
    assert ds[0]["task"] == "transitive_reasoning"

    manifest = split_manifest(a)
    assert manifest["counts"] == {"train": 12, "dev": 4, "blind": 4}
    assert len(manifest["sha256"]) == 64
