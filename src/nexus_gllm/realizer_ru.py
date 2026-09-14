from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

import torch
from torch import nn

from .graph import DynamicHyperGraph
from .schema import AnswerGraph


class DeterministicRussianRealizer:
    def realize(self, answer: AnswerGraph, graph: DynamicHyperGraph) -> str:
        if answer.answer_value is None:
            return "Недостаточно данных для точного ответа."
        if answer.intent == "oldest":
            return f"Самый старший — {answer.answer_value}."
        if answer.intent == "location":
            return f"Находится в: {answer.answer_value}."
        if answer.intent == "ownership":
            return f"Принадлежит: {answer.answer_value}."
        return f"Ответ: {answer.answer_value}."


@dataclass(frozen=True)
class CharVocab:
    tokens: tuple[str, ...]

    PAD = "<PAD>"
    BOS = "<BOS>"
    EOS = "<EOS>"
    UNK = "<UNK>"

    @classmethod
    def from_texts(cls, texts: list[str]) -> "CharVocab":
        chars = sorted({ch for text in texts for ch in text})
        return cls((cls.PAD, cls.BOS, cls.EOS, cls.UNK, *chars))

    def __len__(self) -> int:
        return len(self.tokens)

    @property
    def stoi(self) -> dict[str, int]:
        return {token: i for i, token in enumerate(self.tokens)}

    def encode(self, text: str, add_special: bool = False) -> list[int]:
        table = self.stoi
        ids = [table.get(ch, table[self.UNK]) for ch in text]
        if add_special:
            ids = [table[self.BOS], *ids, table[self.EOS]]
        return ids

    def decode(self, ids: list[int] | tuple[int, ...], skip_special: bool = True) -> str:
        special = {self.PAD, self.BOS, self.EOS, self.UNK}
        chars = []
        for idx in ids:
            token = self.tokens[int(idx)]
            if skip_special and token in special:
                continue
            chars.append(token)
        return "".join(chars)


def answer_graph_vector(answer: AnswerGraph, dim: int = 32) -> torch.Tensor:
    key = f"{answer.intent}|{answer.answer_value}|{answer.confidence:.6f}|{answer.provenance}".encode("utf-8")
    digest = hashlib.sha256(key).digest()
    values = [(digest[i % len(digest)] / 127.5) - 1.0 for i in range(dim)]
    values[0] = float(answer.confidence) * 2.0 - 1.0
    values[1] = 1.0 if answer.answer_value is not None else -1.0
    return torch.tensor(values, dtype=torch.float32)


class NeuralGraphRealizer(nn.Module):
    """Small graph-conditioned GRU surface decoder trained from scratch; not a pretrained LLM."""

    def __init__(self, graph_dim: int, vocab_size: int, hidden_dim: int = 128, emb_dim: int = 64):
        super().__init__()
        self.graph_dim = graph_dim
        self.vocab_size = vocab_size
        self.hidden_dim = hidden_dim
        self.emb_dim = emb_dim
        self.token_emb = nn.Embedding(vocab_size, emb_dim)
        self.graph_to_hidden = nn.Linear(graph_dim, hidden_dim)
        self.gru = nn.GRU(emb_dim, hidden_dim, batch_first=True)
        self.out = nn.Linear(hidden_dim, vocab_size)

    def forward(self, graph_state: torch.Tensor, tokens: torch.Tensor) -> torch.Tensor:
        h0 = torch.tanh(self.graph_to_hidden(graph_state)).unsqueeze(0)
        x = self.token_emb(tokens)
        y, _ = self.gru(x, h0)
        return self.out(y)

    def save_checkpoint(self, path: str | Path, vocab: CharVocab) -> None:
        torch.save({
            "format_version": 1,
            "config": {
                "graph_dim": self.graph_dim,
                "vocab_size": self.vocab_size,
                "hidden_dim": self.hidden_dim,
                "emb_dim": self.emb_dim,
            },
            "vocab": list(vocab.tokens),
            "state_dict": self.state_dict(),
        }, Path(path))

    @classmethod
    def load_checkpoint(cls, path: str | Path) -> tuple["NeuralGraphRealizer", CharVocab]:
        checkpoint = torch.load(Path(path), map_location="cpu", weights_only=False)
        config = checkpoint["config"]
        vocab = CharVocab(tuple(checkpoint["vocab"]))
        if config["vocab_size"] != len(vocab):
            raise ValueError("realizer checkpoint vocabulary size mismatch")
        model = cls(**config)
        model.load_state_dict(checkpoint["state_dict"], strict=True)
        model.eval()
        return model, vocab
