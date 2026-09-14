from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn

from .compiler_proposal import NeuralParseProposal


@dataclass(frozen=True)
class CompilerCharVocab:
    tokens: tuple[str, ...]

    PAD = "<PAD>"
    UNK = "<UNK>"

    @classmethod
    def from_texts(cls, texts: list[str]) -> "CompilerCharVocab":
        chars = sorted({ch for text in texts for ch in text})
        return cls((cls.PAD, cls.UNK, *chars))

    def __len__(self) -> int:
        return len(self.tokens)

    @property
    def stoi(self) -> dict[str, int]:
        return {token: i for i, token in enumerate(self.tokens)}

    def encode(self, text: str) -> list[int]:
        table = self.stoi
        unk = table[self.UNK]
        return [table.get(ch, unk) for ch in text]

    def batch_encode(self, texts: list[str]) -> tuple[torch.Tensor, torch.Tensor]:
        if not texts:
            raise ValueError("texts must be non-empty")
        rows = [self.encode(text) for text in texts]
        max_len = max(len(row) for row in rows)
        if max_len == 0:
            max_len = 1
        pad_id = self.stoi[self.PAD]
        encoded = torch.full((len(rows), max_len), pad_id, dtype=torch.long)
        mask = torch.zeros((len(rows), max_len), dtype=torch.bool)
        for i, row in enumerate(rows):
            if row:
                encoded[i, : len(row)] = torch.tensor(row, dtype=torch.long)
                mask[i, : len(row)] = True
        return encoded, mask


class NeuralRussianGraphCompiler(nn.Module):
    """Character-native structured Russian→Graph proposal model.

    This is intentionally not an autoregressive language model. It predicts a
    relation class, four character-span boundaries and one confidence scalar.
    """

    def __init__(
        self,
        vocab_size: int,
        relation_count: int,
        emb_dim: int = 64,
        hidden_dim: int = 128,
    ) -> None:
        super().__init__()
        if vocab_size < 2 or relation_count < 1:
            raise ValueError("invalid compiler dimensions")
        self.vocab_size = int(vocab_size)
        self.relation_count = int(relation_count)
        self.emb_dim = int(emb_dim)
        self.hidden_dim = int(hidden_dim)

        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.encoder = nn.GRU(
            emb_dim,
            hidden_dim,
            batch_first=True,
            bidirectional=True,
        )
        encoded_dim = hidden_dim * 2
        self.relation_head = nn.Linear(encoded_dim, relation_count)
        self.confidence_head = nn.Linear(encoded_dim, 1)
        self.subject_start_head = nn.Linear(encoded_dim, 1)
        self.subject_end_head = nn.Linear(encoded_dim, 1)
        self.object_start_head = nn.Linear(encoded_dim, 1)
        self.object_end_head = nn.Linear(encoded_dim, 1)

    @staticmethod
    def _masked_pool(encoded: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        weights = mask.to(encoded.dtype).unsqueeze(-1)
        return (encoded * weights).sum(1) / weights.sum(1).clamp_min(1.0)

    @staticmethod
    def _mask_logits(logits: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        return logits.masked_fill(~mask, -1e4)

    def forward(self, tokens: torch.Tensor, mask: torch.Tensor) -> dict[str, torch.Tensor]:
        if tokens.ndim != 2 or mask.shape != tokens.shape:
            raise ValueError("tokens and mask must have shape [batch, length]")
        x = self.embedding(tokens)
        encoded, _ = self.encoder(x)
        pooled = self._masked_pool(encoded, mask)

        return {
            "relation_logits": self.relation_head(pooled),
            "subject_start_logits": self._mask_logits(self.subject_start_head(encoded).squeeze(-1), mask),
            "subject_end_logits": self._mask_logits(self.subject_end_head(encoded).squeeze(-1), mask),
            "object_start_logits": self._mask_logits(self.object_start_head(encoded).squeeze(-1), mask),
            "object_end_logits": self._mask_logits(self.object_end_head(encoded).squeeze(-1), mask),
            "confidence_logit": self.confidence_head(pooled).squeeze(-1),
        }

    @staticmethod
    def _decode_span(start_logits: torch.Tensor, end_logits: torch.Tensor, text_len: int) -> tuple[int, int]:
        if text_len <= 0:
            return (0, 0)
        start = min(int(start_logits[:text_len].argmax()), text_len - 1)
        raw_end = min(int(end_logits[:text_len].argmax()), text_len - 1)
        end = max(start + 1, raw_end + 1)
        end = min(end, text_len)
        return (start, end)

    def predict(
        self,
        text: str,
        vocab: CompilerCharVocab,
        relations: tuple[str, ...],
    ) -> NeuralParseProposal:
        if len(relations) != self.relation_count:
            raise ValueError("relation vocabulary size mismatch")
        tokens, mask = vocab.batch_encode([text])
        self.eval()
        with torch.no_grad():
            out = self(tokens, mask)
        relation_index = int(out["relation_logits"][0].argmax())
        relation = relations[relation_index]
        confidence = float(torch.sigmoid(out["confidence_logit"][0]))
        if relation == "abstain":
            return NeuralParseProposal(
                relation="abstain",
                subject_text=None,
                object_text=None,
                subject_span=None,
                object_span=None,
                confidence=confidence,
                kind="abstain",
            )

        subject_span = self._decode_span(
            out["subject_start_logits"][0], out["subject_end_logits"][0], len(text)
        )
        object_span = self._decode_span(
            out["object_start_logits"][0], out["object_end_logits"][0], len(text)
        )
        return NeuralParseProposal(
            relation=relation,
            subject_text=text[slice(*subject_span)],
            object_text=text[slice(*object_span)],
            subject_span=subject_span,
            object_span=object_span,
            confidence=confidence,
            kind="statement",
        )

    def save_checkpoint(
        self,
        path: str | Path,
        vocab: CompilerCharVocab,
        relations: tuple[str, ...],
        *,
        seed: int,
        manifest_sha: str,
        epoch: int | None = None,
        step: int | None = None,
    ) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "format_version": 1,
                "config": {
                    "vocab_size": self.vocab_size,
                    "relation_count": self.relation_count,
                    "emb_dim": self.emb_dim,
                    "hidden_dim": self.hidden_dim,
                },
                "vocab": list(vocab.tokens),
                "relations": list(relations),
                "state_dict": self.state_dict(),
                "seed": int(seed),
                "manifest_sha": str(manifest_sha),
                "epoch": epoch,
                "step": step,
            },
            Path(path),
        )

    @classmethod
    def load_checkpoint(
        cls, path: str | Path
    ) -> tuple["NeuralRussianGraphCompiler", CompilerCharVocab, tuple[str, ...], dict]:
        checkpoint = torch.load(Path(path), map_location="cpu", weights_only=False)
        config = checkpoint.get("config")
        if not isinstance(config, dict):
            raise ValueError("compiler checkpoint config is missing")
        vocab = CompilerCharVocab(tuple(checkpoint.get("vocab", ())))
        relations = tuple(checkpoint.get("relations", ()))
        if config.get("vocab_size") != len(vocab):
            raise ValueError("compiler checkpoint vocabulary size mismatch")
        if config.get("relation_count") != len(relations):
            raise ValueError("compiler checkpoint relation vocabulary mismatch")
        model = cls(**config)
        state_dict = checkpoint.get("state_dict")
        if not isinstance(state_dict, dict):
            raise ValueError("compiler checkpoint state_dict is missing")
        model.load_state_dict(state_dict, strict=True)
        model.eval()
        meta = {
            "format_version": int(checkpoint.get("format_version", 1)),
            "seed": checkpoint.get("seed"),
            "manifest_sha": checkpoint.get("manifest_sha"),
            "epoch": checkpoint.get("epoch"),
            "step": checkpoint.get("step"),
            "config": dict(config),
        }
        return model, vocab, relations, meta
