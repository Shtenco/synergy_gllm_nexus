from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
import torch.nn.functional as F

from nexus_gllm.realizer_ru import CharVocab, NeuralGraphRealizer, answer_graph_vector
from nexus_gllm.schema import AnswerGraph
from training.dataset import GLLMDataset


def target_text(row: dict) -> tuple[AnswerGraph, str]:
    task = row.get("task")
    answer = row.get("answer")
    if task == "transitive_reasoning":
        graph = AnswerGraph(answer_value=answer, confidence=1.0, intent="oldest", provenance="synthetic")
        return graph, f"Самый старший — {answer}."
    if task == "location_lookup":
        graph = AnswerGraph(answer_value=answer, confidence=1.0, intent="location", provenance="synthetic")
        return graph, f"Находится в: {answer}."
    if task in {"ownership_lookup", "world_revision"}:
        graph = AnswerGraph(answer_value=answer, confidence=1.0, intent="ownership", provenance="synthetic")
        return graph, f"Принадлежит: {answer}."
    graph = AnswerGraph(answer_value=answer, confidence=1.0, intent="identity", provenance="synthetic")
    return graph, f"Ответ: {answer}."


def train(path: Path, out: Path, epochs: int = 4, lr: float = 2e-3, seed: int = 17) -> dict:
    torch.manual_seed(seed)
    ds = GLLMDataset(path, split="train")
    pairs = [target_text(row) for row in ds.rows]
    texts = [text for _, text in pairs]
    vocab = CharVocab.from_texts(texts)
    model = NeuralGraphRealizer(graph_dim=32, vocab_size=len(vocab), hidden_dim=128, emb_dim=64)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    table = vocab.stoi
    last_loss = 0.0
    model.train()

    for _ in range(epochs):
        for answer, text in pairs:
            ids = vocab.encode(text, add_special=True)
            inp = torch.tensor([ids[:-1]], dtype=torch.long)
            target = torch.tensor([ids[1:]], dtype=torch.long)
            graph_state = answer_graph_vector(answer, 32).unsqueeze(0)
            logits = model(graph_state, inp)
            loss = F.cross_entropy(logits.reshape(-1, len(vocab)), target.reshape(-1), ignore_index=table[vocab.PAD])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            last_loss = float(loss.detach())

    out.parent.mkdir(parents=True, exist_ok=True)
    model.save_checkpoint(out, vocab)
    return {"examples": len(pairs), "epochs": epochs, "vocab_size": len(vocab), "last_loss": last_loss, "checkpoint": str(out)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--out", type=Path, default=Path("checkpoints/omega1_realizer.pt"))
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-3)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    print(json.dumps(train(args.data, args.out, args.epochs, args.lr, args.seed), ensure_ascii=False))


if __name__ == "__main__":
    main()
