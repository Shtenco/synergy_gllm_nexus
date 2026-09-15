from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import torch

_WORD_RE = re.compile(r"[\wА-Яа-яЁё_]+", re.UNICODE)


def enumerate_candidates(text: str, max_words: int = 2) -> list[tuple[int, int]]:
    words = [m.span() for m in _WORD_RE.finditer(text)]
    out: list[tuple[int, int]] = []
    for i in range(len(words)):
        for width in range(1, max_words + 1):
            j = i + width - 1
            if j < len(words):
                out.append((words[i][0], words[j][1]))
    return out


def morph_features(text: str, max_len: int) -> torch.Tensor:
    out = torch.zeros((max_len, 6), dtype=torch.float32)
    for i, ch in enumerate(text[:max_len]):
        category = unicodedata.category(ch)
        out[i, 0] = float(ch.isalpha())
        out[i, 1] = float(ch.isdigit())
        out[i, 2] = float(ch.isupper())
        out[i, 3] = float(ch.isspace())
        out[i, 4] = float(category.startswith("P"))
        prev_boundary = (
            i == 0
            or text[i - 1].isspace()
            or unicodedata.category(text[i - 1]).startswith("P")
        )
        out[i, 5] = float(prev_boundary)
    return out


@dataclass(frozen=True)
class CandidateVocab:
    tokens: tuple[str, ...]

    PAD = "<PAD>"
    UNK = "<UNK>"

    @classmethod
    def from_texts(cls, texts: list[str]) -> "CandidateVocab":
        chars = sorted({ch for text in texts for ch in text})
        return cls((cls.PAD, cls.UNK, *chars))

    def __len__(self) -> int:
        return len(self.tokens)

    @property
    def stoi(self) -> dict[str, int]:
        return {token: i for i, token in enumerate(self.tokens)}

    def morph_table(self) -> torch.Tensor:
        table = torch.zeros((len(self.tokens), 6), dtype=torch.float32)
        for i, token in enumerate(self.tokens):
            if len(token) != 1:
                continue
            ch = token
            category = unicodedata.category(ch)
            table[i, 0] = float(ch.isalpha())
            table[i, 1] = float(ch.isdigit())
            table[i, 2] = float(ch.isupper())
            table[i, 3] = float(ch.isspace())
            table[i, 4] = float(category.startswith("P"))
            table[i, 5] = float(ch.isspace() or category.startswith("P"))
        return table

    def batch_encode(self, texts: list[str], max_len: int = 96) -> dict[str, torch.Tensor]:
        table = self.stoi
        unk = table[self.UNK]
        pad = table[self.PAD]
        tokens = torch.full((len(texts), max_len), pad, dtype=torch.long)
        mask = torch.zeros((len(texts), max_len), dtype=torch.bool)
        morph = torch.zeros((len(texts), max_len, 6), dtype=torch.float32)
        for batch_index, text in enumerate(texts):
            ids = [table.get(ch, unk) for ch in text[:max_len]]
            if ids:
                tokens[batch_index, : len(ids)] = torch.tensor(ids)
                mask[batch_index, : len(ids)] = True
                morph[batch_index] = morph_features(text, max_len)
        return {"tokens": tokens, "mask": mask, "morph": morph}
