from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

from nexus_gllm.unified_v2.organs.semantic_supplement import SemanticSupplement


class ArtifactUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class MCQAnswer:
    answer: str | None
    stage: str | None
    source: str
    artifact_sha256: str


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_module(path: Path, *, expected_sha256: str | None = None) -> tuple[ModuleType, str]:
    path = Path(path)
    if not path.is_file():
        raise ArtifactUnavailable(f"missing donor artifact: {path}")
    digest = _sha256(path)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ArtifactUnavailable(f"donor digest mismatch for {path}: {digest} != {expected_sha256}")
    name = "nexus_v2_donor_" + digest[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ArtifactUnavailable(f"cannot load donor module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, digest


class FormalAuthorityAdapter:
    organ_id = "formal_authority"
    source_version = "R7.8"

    def __init__(self, module_path: Path, *, expected_sha256: str | None = None):
        self.module, self.artifact_sha256 = _load_module(module_path, expected_sha256=expected_sha256)
        if not hasattr(self.module, "solve"):
            raise ArtifactUnavailable("R7.8 donor has no solve(item) contract")

    def answer_mcq(self, item: dict) -> MCQAnswer:
        raw = self.module.solve(item)
        if isinstance(raw, tuple):
            answer, stage = raw[0], raw[1] if len(raw) > 1 else None
        elif isinstance(raw, dict):
            answer, stage = raw.get("answer"), raw.get("stage") or raw.get("status")
        else:
            answer, stage = raw, None
        if answer not in {"A", "B", "C", "D"}:
            answer = None
        return MCQAnswer(answer, stage, self.source_version, self.artifact_sha256)


class EvidenceSemanticAdapter:
    organ_id = "evidence_governor"
    source_version = "R7.18"

    def __init__(self, module_path: Path, *, expected_sha256: str | None = None):
        self.module, self.artifact_sha256 = _load_module(module_path, expected_sha256=expected_sha256)
        if not hasattr(self.module, "decide"):
            raise ArtifactUnavailable("R7.18 donor has no decide(item, teachers) contract")
        self.supplement = SemanticSupplement()

    def answer_mcq(self, item: dict) -> MCQAnswer:
        raw = self.module.decide(item, {})
        if not isinstance(raw, dict):
            raw = {}
        answer = raw.get("answer")
        stage = raw.get("stage") or raw.get("status")
        if answer in {"A", "B", "C", "D"}:
            return MCQAnswer(answer, stage, self.source_version, self.artifact_sha256)
        fallback = self.supplement.answer_mcq(item.get("q", ""), item.get("options", {}))
        if fallback is not None:
            return MCQAnswer(fallback, "V2_SEMANTIC_SUPPLEMENT_AFTER_R718_ABSTAIN", "Unified-v2 SemanticSupplement", self.artifact_sha256)
        return MCQAnswer(None, stage, self.source_version, self.artifact_sha256)

@dataclass(frozen=True)
class RoleParse:
    relation: str
    subject: str | None
    object: str | None
    semantic_sha256: str
    joint_sha256: str


class Omega15R2RoleAdapter:
    organ_id = "role_binder"
    source_version = "Omega-1.5R2"

    def __init__(self, bundle_root: Path, *, unified_rebuild_root: Path | None = None):
        import sys
        import joblib

        self.bundle_root = Path(bundle_root)
        semantic_path = self.bundle_root / "artifacts/base_semantic/omega14r_semantic_operator.joblib"
        joint_path = self.bundle_root / "artifacts/omega15r2_v1/omega15r2_joint_binder_frozen.joblib"
        if not semantic_path.is_file() or not joint_path.is_file():
            raise ArtifactUnavailable(f"missing Omega-1.5R2 checkpoint(s) under {self.bundle_root}")
        if unified_rebuild_root is None:
            candidate = Path("/mnt/data/nexus_ub1_src/unified/nexus_unified_rebuild_v1")
            unified_rebuild_root = candidate if candidate.is_dir() else None
        search = [self.bundle_root]
        if unified_rebuild_root is not None:
            search.insert(0, Path(unified_rebuild_root))
        for path in reversed(search):
            text = str(path)
            if text not in sys.path:
                sys.path.insert(0, text)
        try:
            import rebuild_models  # noqa: F401
            import omega15r2.joint_r2  # noqa: F401
            import omega15r2.pair_binder  # noqa: F401
            import omega15r2.direction_factor  # noqa: F401
            self.semantic = joblib.load(semantic_path)
            self.joint = joblib.load(joint_path)
        except Exception as exc:
            raise ArtifactUnavailable(f"cannot load Omega-1.5R2 artifacts: {exc}") from exc
        self.semantic_sha256 = _sha256(semantic_path)
        self.joint_sha256 = _sha256(joint_path)

    def parse(self, text: str) -> RoleParse:
        relation = self.semantic.predict([text])[0]
        if relation == "abstain":
            return RoleParse(relation, None, None, self.semantic_sha256, self.joint_sha256)
        result = self.joint.predict_one(text, relation)
        return RoleParse(relation, result.get("subject"), result.get("object"), self.semantic_sha256, self.joint_sha256)

@dataclass(frozen=True)
class UnifiedArtifactIdentity:
    semantic_sha256: str
    argument_sha256: str
    context_sha256: str


class UnifiedRebuildAdapter:
    organ_id = "unified_graph_workspace"
    source_version = "Unified NEXUS Rebuild v1"

    def __init__(self, root: Path):
        import sys
        root = Path(root)
        runtime_path = root / "unified_runtime.py"
        checkpoint_dir = root / "artifacts/checkpoints_v1"
        required = [
            checkpoint_dir / "omega14r_semantic_operator.joblib",
            checkpoint_dir / "omega15r_joint_argument.joblib",
            checkpoint_dir / "context_revision_binder_r.joblib",
        ]
        if not runtime_path.is_file() or not all(p.is_file() for p in required):
            raise ArtifactUnavailable(f"missing Unified Rebuild runtime/checkpoints under {root}")
        root_text = str(root)
        if root_text not in sys.path:
            sys.path.insert(0, root_text)
        try:
            module, runtime_sha = _load_module(runtime_path)
            self.runtime_class = module.UnifiedNexusRuntime
            self.checkpoint_dir = checkpoint_dir
            self.runtime_sha256 = runtime_sha
            self.identity = UnifiedArtifactIdentity(*(_sha256(p) for p in required))
            self._probe = self.runtime_class(self.checkpoint_dir)
        except Exception as exc:
            raise ArtifactUnavailable(f"cannot load Unified Rebuild v1: {exc}") from exc

    def new_runtime(self, *, with_checkpoints: bool = False):
        return self.runtime_class(self.checkpoint_dir if with_checkpoints else None)

    def parse_ru(self, text: str) -> dict:
        return self._probe.parse_ru(text)

    def resolve_graph(self, facts, query) -> dict:
        rt = self.new_runtime()
        for relation, subject, obj in facts:
            rt.upsert(relation, subject, obj, source="v2-adapter")
        relation, subject, _ = query
        return rt.query(subject, relation)
