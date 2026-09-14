from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


class GLLMDataset:
    def __init__(self, path: str | Path, split: str | None = None) -> None:
        rows = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if split is None or row.get("split") == split:
                rows.append(row)
        self.rows = rows

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        return self.rows[index]


def split_manifest(records: Iterable[dict]) -> dict:
    rows = list(records)
    counts = {name: sum(1 for r in rows if r.get("split") == name) for name in ("train", "dev", "blind")}
    canonical = "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for r in rows)
    return {
        "counts": counts,
        "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }
