from __future__ import annotations

from dataclasses import dataclass
import torch
from torch import nn


@dataclass
class GraphTensorBatch:
    node_states: torch.Tensor
    edge_index: torch.Tensor
    edge_types: torch.Tensor
    node_mask: torch.Tensor


@dataclass
class GraphRecurrentOutput:
    node_states: torch.Tensor
    operation_logits: torch.Tensor


class GraphRecurrentCore(nn.Module):
    def __init__(self, node_dim: int, edge_types: int, hidden_dim: int, op_count: int = 6):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.node_in = nn.Linear(node_dim, hidden_dim)
        self.edge_embed = nn.Embedding(edge_types, hidden_dim)
        self.msg = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
        )
        self.global_proj = nn.Linear(hidden_dim, hidden_dim)
        self.update = nn.GRUCell(hidden_dim * 2, hidden_dim)
        self.activation_head = nn.Linear(hidden_dim, 1)
        self.op_head = nn.Sequential(nn.LayerNorm(hidden_dim), nn.Linear(hidden_dim, op_count))

    def _messages(self, h: torch.Tensor, edge_index: torch.Tensor, edge_types: torch.Tensor) -> torch.Tensor:
        batch_size, node_count, _ = h.shape
        agg = torch.zeros_like(h)
        for b in range(batch_size):
            if edge_index.numel() == 0 or edge_index.shape[1] == 0:
                continue
            src = edge_index[b, :, 0]
            dst = edge_index[b, :, 1]
            edge_h = self.edge_embed(edge_types[b])
            messages = self.msg(torch.cat([h[b, src], edge_h], dim=-1))
            agg[b].index_add_(0, dst, messages)
        return agg

    def forward(self, batch: GraphTensorBatch, steps: int = 3) -> GraphRecurrentOutput:
        if steps < 1:
            raise ValueError("steps must be >= 1")
        h = self.node_in(batch.node_states)
        mask = batch.node_mask.unsqueeze(-1).to(h.dtype)
        h = h * mask
        for _ in range(steps):
            agg = self._messages(h, batch.edge_index, batch.edge_types)
            denom = mask.sum(dim=1).clamp_min(1.0)
            global_state = (h * mask).sum(dim=1) / denom
            broadcast = self.global_proj(global_state).unsqueeze(1).expand_as(h)
            inp = torch.cat([agg, broadcast], dim=-1)
            h = self.update(inp.reshape(-1, inp.shape[-1]), h.reshape(-1, h.shape[-1])).view_as(h)
            gate = torch.sigmoid(self.activation_head(h))
            h = h * gate * mask
        pooled = (h * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)
        return GraphRecurrentOutput(node_states=h, operation_logits=self.op_head(pooled))
