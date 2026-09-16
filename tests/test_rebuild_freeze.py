from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from nexus_gllm.rebuild_freeze import (
    build_freeze_manifest,
    sha256_file,
    verify_freeze_manifest,
)


def test_sha256_file_matches_reference(tmp_path: Path) -> None:
    payload = tmp_path / "payload.bin"
    payload.write_bytes(b"NEXUS-REBUILD-V1\n")
    assert sha256_file(payload) == hashlib.sha256(payload.read_bytes()).hexdigest()


def test_freeze_manifest_is_canonical_and_verifiable(tmp_path: Path) -> None:
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("alpha\n", encoding="utf-8")
    b.write_text("beta\n", encoding="utf-8")

    manifest = build_freeze_manifest(
        artifact_name="omega14-rebuild-v1",
        files={"weights": a, "protocol": b},
        metadata={"seed": 1701, "architecture": "omega14_semantic_operator_cortex_rebuild_v1"},
    )

    assert manifest["format_version"] == 1
    assert manifest["artifact_name"] == "omega14-rebuild-v1"
    assert list(manifest["files"]) == ["protocol", "weights"]
    assert manifest["metadata"]["seed"] == 1701
    assert verify_freeze_manifest(manifest, base_dir=tmp_path) == []

    # Canonical JSON must be stable enough to hash into an integration manifest.
    encoded = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert hashlib.sha256(encoded).hexdigest()


def test_freeze_manifest_detects_tampering(tmp_path: Path) -> None:
    payload = tmp_path / "weights.pt"
    payload.write_bytes(b"original")
    manifest = build_freeze_manifest(
        artifact_name="omega15-rebuild-v1",
        files={"weights": payload},
        metadata={"seed": 1702},
    )

    payload.write_bytes(b"tampered")
    errors = verify_freeze_manifest(manifest, base_dir=tmp_path)
    assert errors
    assert any("sha256" in error for error in errors)


def test_freeze_manifest_rejects_missing_file(tmp_path: Path) -> None:
    payload = tmp_path / "weights.pt"
    payload.write_bytes(b"x")
    manifest = build_freeze_manifest(
        artifact_name="unified-nexus-rebuild-v1",
        files={"weights": payload},
        metadata={},
    )
    payload.unlink()

    errors = verify_freeze_manifest(manifest, base_dir=tmp_path)
    assert errors == ["missing file: weights.pt"]


def test_freeze_manifest_rejects_paths_outside_base_dir(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.bin"
    outside.write_bytes(b"x")
    try:
        with pytest.raises(ValueError):
            build_freeze_manifest(
                artifact_name="bad",
                files={"weights": outside},
                metadata={},
                base_dir=tmp_path,
            )
    finally:
        outside.unlink(missing_ok=True)
