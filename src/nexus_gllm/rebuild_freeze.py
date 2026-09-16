from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping


def sha256_file(path: str | Path) -> str:
    source = Path(path)
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(path: Path, base_dir: Path) -> str:
    resolved_base = base_dir.resolve()
    resolved_path = path.resolve()
    try:
        relative = resolved_path.relative_to(resolved_base)
    except ValueError as exc:
        raise ValueError(f"file is outside base_dir: {path}") from exc
    return relative.as_posix()


def build_freeze_manifest(
    *,
    artifact_name: str,
    files: Mapping[str, str | Path],
    metadata: Mapping[str, object],
    base_dir: str | Path | None = None,
) -> dict:
    if not artifact_name.strip():
        raise ValueError("artifact_name must be non-empty")
    if not files:
        raise ValueError("files must be non-empty")

    paths = {name: Path(path) for name, path in files.items()}
    if base_dir is None:
        parents = [path.resolve().parent for path in paths.values()]
        common = Path(__import__("os").path.commonpath([str(parent) for parent in parents]))
    else:
        common = Path(base_dir).resolve()

    frozen_files: dict[str, dict[str, object]] = {}
    for logical_name in sorted(paths):
        path = paths[logical_name]
        if not path.is_file():
            raise FileNotFoundError(path)
        relative = _safe_relative(path, common)
        frozen_files[logical_name] = {
            "path": relative,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    return {
        "format_version": 1,
        "artifact_name": artifact_name,
        "files": frozen_files,
        "metadata": dict(metadata),
    }


def verify_freeze_manifest(manifest: Mapping[str, object], *, base_dir: str | Path) -> list[str]:
    root = Path(base_dir).resolve()
    errors: list[str] = []
    files = manifest.get("files")
    if not isinstance(files, Mapping):
        return ["manifest files section is invalid"]

    for logical_name in sorted(files):
        record = files[logical_name]
        if not isinstance(record, Mapping):
            errors.append(f"invalid file record: {logical_name}")
            continue
        relative = record.get("path")
        if not isinstance(relative, str):
            errors.append(f"invalid path: {logical_name}")
            continue
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            errors.append(f"unsafe path: {relative}")
            continue
        if not candidate.is_file():
            errors.append(f"missing file: {relative}")
            continue
        expected_bytes = record.get("bytes")
        if isinstance(expected_bytes, int) and candidate.stat().st_size != expected_bytes:
            errors.append(f"bytes mismatch: {relative}")
        expected_sha = record.get("sha256")
        actual_sha = sha256_file(candidate)
        if expected_sha != actual_sha:
            errors.append(f"sha256 mismatch: {relative}")
    return errors
