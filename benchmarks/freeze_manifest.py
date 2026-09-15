from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def freeze(path: Path, seed: int) -> dict:
    payload = path.read_bytes()
    manifest = {
        "benchmark": str(path),
        "seed": seed,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }
    out = path.with_suffix(path.suffix + ".freeze.json")
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.path, args.seed), ensure_ascii=False))


if __name__ == "__main__":
    main()
