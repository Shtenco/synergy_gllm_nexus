from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import os

import torch
from torch import nn

from .capability_router import HeuristicCapabilityRouter, RouterFeatures
from .contracts import RoutingDecision

P1_EXPERTS = ("r7l", "r72", "r718", "r744", "graph", "v3")
P1_FEATURES = ("support", "ru", "evidence", "context", "graph", "novelty", "proof", "cost")
P1_SHA256 = {
    "router.pt": "64ed453c3360c863ec7411d7c2d76afd85db93b4353fbb0f716f663fc789190b",
    "novelty.pt": "bb2fd3cbfdc8491cc242d29fbe6b5c667900cfb034f3f89c1e833968a9418a4d",
    "calibrator.pt": "d3ad93337c6d45f5dbb698686697689b67cc475ea7547025d3fe5a0f209f374a",
    "manifest.json": "c4cdac2dfd56b339a2eb06f3dcd7db521cc738fd50a9e54219079d9fb655fc10",
    "metrics.json": "2060fd60b09120f4d8e2922f6a9840f1d34fb8082366fcca5a7698b9c0212157",
}

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))

class _RouterNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.m = nn.Sequential(nn.Linear(8, 32), nn.Tanh(), nn.Linear(32, 6))
    def forward(self, x):
        return self.m(x)

class _Calibrator(nn.Module):
    def __init__(self):
        super().__init__()
        self.scale = nn.Parameter(torch.ones(6))
        self.bias = nn.Parameter(torch.zeros(6))
    def forward(self, scores):
        return scores * self.scale + self.bias

class _NoveltyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.m = nn.Sequential(nn.Linear(8, 12), nn.ReLU(), nn.Linear(12, 1))
    def forward(self, x):
        return self.m(x).squeeze(-1)

@dataclass(frozen=True)
class RouterLoadStatus:
    source: str
    loaded: bool
    reason: str = ""
    artifact_dir: str | None = None

class LoadableCapabilityRouter:
    """Frozen P1 learned router with an explicit fail-closed heuristic fallback.

    P1 and B1 are intentionally distinct. This loader consumes the six-expert
    P1 router, never the seven-expert B1 router.
    """
    def __init__(self, artifact_dir=None, *, expected_sha256=None, verify_hashes=True, heuristic=None):
        self.heuristic = heuristic or HeuristicCapabilityRouter()
        self.router = None
        self.calibrator = None
        self.novelty = None
        self.metrics = None
        self.manifest = None
        self._verify_hashes = verify_hashes
        self._expected = dict(P1_SHA256 if expected_sha256 is None else expected_sha256)
        self.artifact_dir = self._resolve_dir(artifact_dir)
        self.status = self._load()

    @staticmethod
    def _resolve_dir(explicit):
        if explicit is not None:
            return Path(explicit)
        env = os.getenv("NEXUS_MOE_P1_DIR")
        if env:
            return Path(env)
        repo_root = Path(__file__).resolve().parents[4]
        return repo_root / "artifacts" / "v3_moe" / "p1"

    def _load(self):
        try:
            required = tuple(P1_SHA256)
            missing = [n for n in required if not (self.artifact_dir / n).is_file()]
            if missing:
                return RouterLoadStatus("heuristic_fallback", False, "missing:" + ",".join(missing), str(self.artifact_dir))
            if self._verify_hashes:
                bad = [n for n in required if n in self._expected and _sha256(self.artifact_dir / n) != self._expected[n]]
                if bad:
                    return RouterLoadStatus("heuristic_fallback", False, "sha256_mismatch:" + ",".join(bad), str(self.artifact_dir))
            manifest = json.loads((self.artifact_dir / "manifest.json").read_text(encoding="utf-8"))
            if tuple(manifest.get("features", ())) != P1_FEATURES:
                return RouterLoadStatus("heuristic_fallback", False, "manifest_feature_mismatch", str(self.artifact_dir))
            if tuple(manifest.get("experts", ())) != P1_EXPERTS:
                return RouterLoadStatus("heuristic_fallback", False, "manifest_expert_mismatch", str(self.artifact_dir))
            router, calibrator, novelty = _RouterNet(), _Calibrator(), _NoveltyNet()
            router.load_state_dict(torch.load(self.artifact_dir / "router.pt", map_location="cpu", weights_only=True))
            calibrator.load_state_dict(torch.load(self.artifact_dir / "calibrator.pt", map_location="cpu", weights_only=True))
            novelty.load_state_dict(torch.load(self.artifact_dir / "novelty.pt", map_location="cpu", weights_only=True))
            router.eval(); calibrator.eval(); novelty.eval()
            self.router, self.calibrator, self.novelty = router, calibrator, novelty
            self.manifest = manifest
            self.metrics = json.loads((self.artifact_dir / "metrics.json").read_text(encoding="utf-8"))
            return RouterLoadStatus("learned_p1", True, "verified", str(self.artifact_dir))
        except Exception as exc:
            self.router = self.calibrator = self.novelty = None
            return RouterLoadStatus("heuristic_fallback", False, f"load_error:{type(exc).__name__}", str(self.artifact_dir))

    @staticmethod
    def feature_vector(f: RouterFeatures):
        ru = (1.0 if f.language == "ru" else 0.0) if f.ru_signal is None else _clamp01(f.ru_signal)
        evidence = (1.0 if f.evidence_conflict else 0.0) if f.evidence_signal is None else _clamp01(f.evidence_signal)
        return (
            _clamp01(f.support_count / 4.0),
            ru,
            evidence,
            _clamp01(f.context_depth / 4.0),
            _clamp01(f.graph_signal),
            _clamp01(f.novelty),
            _clamp01(f.proof_signal),
            _clamp01(getattr(f, "cost_signal", 0.0)),
        )

    def novelty_probability(self, f):
        if not self.status.loaded:
            return None
        x = torch.tensor([self.feature_vector(f)], dtype=torch.float32)
        with torch.no_grad():
            return float(torch.sigmoid(self.novelty(x))[0])

    def route(self, f, registry, k_min=2, k_max=4):
        if not self.status.loaded:
            return self.heuristic.route(f, registry, k_min, k_max)
        active = {s.expert_id for s in registry.active()}
        if not set(P1_EXPERTS).issubset(active):
            return self.heuristic.route(f, registry, k_min, k_max)
        x = torch.tensor([self.feature_vector(f)], dtype=torch.float32)
        with torch.no_grad():
            logits = self.router(x)
            probs = torch.sigmoid(self.calibrator(logits))[0].tolist()
            novelty_p = float(torch.sigmoid(self.novelty(x))[0])
        scored = tuple(sorted(zip(P1_EXPERTS, probs), key=lambda item: (-item[1], item[0])))
        target = 4 if novelty_p >= 0.5 else 3
        k = max(k_min, min(k_max, target))
        selected = tuple(eid for eid, _ in scored if eid in active)[:k]
        if len(selected) < k_min:
            return self.heuristic.route(f, registry, k_min, k_max)
        return RoutingDecision(selected, scored, widened=(k > 3))
