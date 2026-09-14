from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch
import torch.nn.functional as F

from nexus_gllm.recurrent import GraphRecurrentCore, GraphTensorBatch
from training.dataset import GLLMDataset

OP_ANSWER = 5


def _vec(label: str, dim: int) -> torch.Tensor:
    digest = hashlib.sha256(label.encode("utf-8")).digest()
    values = [(digest[i % len(digest)] / 127.5) - 1.0 for i in range(dim)]
    return torch.tensor(values, dtype=torch.float32)


def record_to_batch(record: dict, node_dim: int = 32) -> GraphTensorBatch:
    entities = record["entities"]
    node_states = torch.stack([_vec(name, node_dim) for name in entities], dim=0).unsqueeze(0)
    edge_index = torch.tensor([[[0, 1], [1, 2]]], dtype=torch.long)
    edge_types = torch.tensor([[1, 1]], dtype=torch.long)
    node_mask = torch.ones(1, len(entities), dtype=torch.bool)
    return GraphTensorBatch(node_states=node_states, edge_index=edge_index, edge_types=edge_types, node_mask=node_mask)


def train(path: Path, out: Path, epochs: int = 3, lr: float = 3e-3, seed: int = 17) -> dict:
    torch.manual_seed(seed)
    dataset = GLLMDataset(path, split="train")
    if not len(dataset):
        raise ValueError("training split is empty")
    model = GraphRecurrentCore(node_dim=32, edge_types=8, hidden_dim=64, op_count=6)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    last_loss = 0.0
    model.train()
    for _ in range(epochs):
        for row in dataset.rows:
            batch = record_to_batch(row)
            logits = model(batch, steps=3).operation_logits
            target = torch.tensor([OP_ANSWER], dtype=torch.long)
            loss = F.cross_entropy(logits, target)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            last_loss = float(loss.detach())
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "config": {"node_dim": 32, "edge_types": 8, "hidden_dim": 64, "op_count": 6}, "seed": seed, "epochs": epochs}, out)
    return {"examples": len(dataset), "epochs": epochs, "last_loss": last_loss, "checkpoint": str(out)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--out", type=Path, default=Path("checkpoints/omega1_core.pt"))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=3e-3)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    print(json.dumps(train(args.data, args.out, args.epochs, args.lr, args.seed), ensure_ascii=False))


if __name__ == "__main__":
    main()
