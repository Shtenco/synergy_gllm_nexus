from __future__ import annotations
import hashlib
import math
from pathlib import Path
from typing import Callable, Sequence

import torch
import torch.nn as nn

from .types import CortexDecisionFeatures

EXPECTED_SHA256 = "5a2c0c74cc25a9d4a17dc3575e299c8fbd2ed6b7a3115ebba439ba93484cfdfa"


def _sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _entropy(p: torch.Tensor) -> float:
    p = p.clamp_min(1e-12)
    return float((-(p * p.log()).sum()).item())


class _RecoveredV72(nn.Module):
    """State-dict-compatible reconstruction of recovered V7.2 cognitive encoder.

    Attention head count is not recoverable from a PyTorch state_dict, so it is
    explicit and preserved in provenance rather than silently claimed as exact.
    """
    def __init__(self, *, nhead: int = 8):
        super().__init__()
        d_model = 320
        if d_model % nhead:
            raise ValueError("nhead must divide 320")
        self.emb = nn.Embedding(16385, d_model)
        self.pos = nn.Embedding(112, d_model)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=1536,
            dropout=0.0, activation="gelu", batch_first=True, norm_first=False,
        )
        self.enc = nn.TransformerEncoder(layer, num_layers=6)
        self.norm = nn.LayerNorm(d_model)
        self.plan = nn.Sequential(
            nn.Linear(d_model, d_model), nn.GELU(), nn.LayerNorm(d_model), nn.Linear(d_model, 14)
        )
        self.rel = nn.Linear(d_model, 2)
        self.role = nn.Linear(d_model, 8)
        self.temp = nn.Linear(d_model, 3)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor | None = None):
        if input_ids.ndim != 2:
            raise ValueError("input_ids must be [batch, seq]")
        b, t = input_ids.shape
        if t > 112:
            raise ValueError("sequence length exceeds recovered max_positions=112")
        if input_ids.min().item() < 0 or input_ids.max().item() >= 16385:
            raise ValueError("token id outside recovered vocab range")
        pos = torch.arange(t, device=input_ids.device).unsqueeze(0).expand(b, t)
        x = self.emb(input_ids) + self.pos(pos)
        padding_mask = None
        if attention_mask is not None:
            if attention_mask.shape != input_ids.shape:
                raise ValueError("attention_mask shape mismatch")
            padding_mask = attention_mask == 0
        z = self.norm(self.enc(x, src_key_padding_mask=padding_mask))
        if attention_mask is None:
            pooled = z.mean(dim=1)
        else:
            w = attention_mask.to(z.dtype).unsqueeze(-1)
            pooled = (z * w).sum(dim=1) / w.sum(dim=1).clamp_min(1.0)
        return self.plan(pooled), self.rel(pooled), self.role(pooled), self.temp(pooled)


class V72CortexAdapter:
    def __init__(self, checkpoint_path: str | Path, *, expected_sha256: str = EXPECTED_SHA256,
                 nhead: int = 8, exact_source_reconstruction: bool = False, device: str = "cpu"):
        self.path = Path(checkpoint_path)
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        actual = _sha256(self.path)
        if actual != expected_sha256:
            raise ValueError(f"checkpoint SHA-256 mismatch: {actual}")
        raw = torch.load(self.path, map_location="cpu", weights_only=False)
        if not isinstance(raw, dict) or "state_dict" not in raw or "meta" not in raw:
            raise ValueError("unsupported V7.2 checkpoint structure")
        sd = raw["state_dict"]
        self._validate_state_dict(sd)
        self.meta = dict(raw["meta"])
        self.checkpoint_sha256 = actual
        self.nhead = int(nhead)
        self.exact_source_reconstruction = bool(exact_source_reconstruction)
        self.model = _RecoveredV72(nhead=self.nhead)
        missing, unexpected = self.model.load_state_dict(sd, strict=False)
        if missing or unexpected:
            raise ValueError(f"state_dict mismatch: missing={missing}, unexpected={unexpected}")
        self.device = torch.device(device)
        self.model.to(self.device).eval()

    @staticmethod
    def _validate_state_dict(sd):
        checks = {
            "emb.weight": (16385, 320), "pos.weight": (112, 320),
            "plan.3.weight": (14, 320), "rel.weight": (2, 320),
            "role.weight": (8, 320), "temp.weight": (3, 320),
            "norm.weight": (320,), "norm.bias": (320,),
        }
        for key, shape in checks.items():
            if key not in sd or tuple(sd[key].shape) != shape:
                raise ValueError(f"unexpected V7.2 tensor shape for {key}")

    @torch.inference_mode()
    def infer_token_ids(self, token_ids: Sequence[int]) -> CortexDecisionFeatures:
        if not token_ids:
            raise ValueError("token_ids must not be empty")
        ids = torch.tensor([list(map(int, token_ids))], dtype=torch.long, device=self.device)
        mask = torch.ones_like(ids)
        logits = self.model(ids, mask)
        probs = [torch.softmax(x[0].float().cpu(), dim=-1) for x in logits]
        entropies = [_entropy(p) for p in probs]
        normalized_entropy = [e / math.log(len(p)) for e, p in zip(entropies, probs)]
        uncertainty = float(sum(normalized_entropy) / len(normalized_entropy))
        return CortexDecisionFeatures(
            plan_probs=tuple(float(x) for x in probs[0]), relation_probs=tuple(float(x) for x in probs[1]),
            role_probs=tuple(float(x) for x in probs[2]), temporal_probs=tuple(float(x) for x in probs[3]),
            plan_entropy=entropies[0], relation_entropy=entropies[1], role_entropy=entropies[2],
            temporal_entropy=entropies[3], uncertainty=uncertainty,
            checkpoint_sha256=self.checkpoint_sha256, checkpoint_name=str(self.meta.get("name", "")),
            reconstruction_nhead=self.nhead, reconstruction_exact_source=self.exact_source_reconstruction,
        )

    def infer_text(self, text: str, tokenizer: Callable[[str], Sequence[int]]) -> CortexDecisionFeatures:
        if not callable(tokenizer):
            raise TypeError("tokenizer must be callable")
        return self.infer_token_ids(tokenizer(text))
