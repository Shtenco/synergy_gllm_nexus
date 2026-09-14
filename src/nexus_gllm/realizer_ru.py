from __future__ import annotations

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


class NeuralGraphRealizer(nn.Module):
    """Small graph-conditioned decoder; not a pretrained language model."""

    def __init__(self, graph_dim: int, vocab_size: int, hidden_dim: int = 128, emb_dim: int = 64):
        super().__init__()
        self.token_emb = nn.Embedding(vocab_size, emb_dim)
        self.graph_to_hidden = nn.Linear(graph_dim, hidden_dim)
        self.gru = nn.GRU(emb_dim, hidden_dim, batch_first=True)
        self.out = nn.Linear(hidden_dim, vocab_size)

    def forward(self, graph_state: torch.Tensor, tokens: torch.Tensor) -> torch.Tensor:
        h0 = torch.tanh(self.graph_to_hidden(graph_state)).unsqueeze(0)
        x = self.token_emb(tokens)
        y, _ = self.gru(x, h0)
        return self.out(y)
