from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch
import torch.nn.functional as F

from nexus_gllm.compiler_neural import CompilerCharVocab, NeuralRussianGraphCompiler
from training.dataset import GLLMDataset


DEFAULT_RELATIONS = (
    "is_a",
    "older_than",
    "located_in",
    "owned_by",
    "before",
    "causes",
    "abstain",
)


def build_compiler_from_records(
    records: list[dict],
    *,
    emb_dim: int = 64,
    hidden_dim: int = 128,
    relations: tuple[str, ...] = DEFAULT_RELATIONS,
) -> tuple[NeuralRussianGraphCompiler, CompilerCharVocab, tuple[str, ...]]:
    if not records:
        raise ValueError("compiler training records must be non-empty")
    vocab = CompilerCharVocab.from_texts([row["input_text"] for row in records])
    model = NeuralRussianGraphCompiler(
        vocab_size=len(vocab),
        relation_count=len(relations),
        emb_dim=emb_dim,
        hidden_dim=hidden_dim,
    )
    return model, vocab, relations


def compute_example_loss(
    model: NeuralRussianGraphCompiler,
    vocab: CompilerCharVocab,
    relations: tuple[str, ...],
    row: dict,
) -> dict[str, torch.Tensor]:
    text = row["input_text"]
    target = row["compiler_target"]
    relation = target["relation"]
    if relation not in relations:
        raise ValueError(f"target relation not in vocabulary: {relation}")

    tokens, mask = vocab.batch_encode([text])
    out = model(tokens, mask)
    relation_target = torch.tensor([relations.index(relation)], dtype=torch.long)
    confidence_target = torch.tensor([float(target.get("confidence", 1.0))], dtype=torch.float32)

    losses: dict[str, torch.Tensor] = {
        "relation": F.cross_entropy(out["relation_logits"], relation_target),
        "confidence": F.binary_cross_entropy_with_logits(out["confidence_logit"], confidence_target),
    }

    if relation != "abstain":
        subject_span = target["subject_span"]
        object_span = target["object_span"]
        if subject_span is None or object_span is None:
            raise ValueError("non-abstain target requires subject/object spans")
        positions = {
            "subject_start": int(subject_span[0]),
            "subject_end": int(subject_span[1]) - 1,
            "object_start": int(object_span[0]),
            "object_end": int(object_span[1]) - 1,
        }
        for name, position in positions.items():
            logits = out[f"{name}_logits"]
            if position < 0 or position >= logits.shape[1]:
                raise ValueError(f"{name} target out of bounds")
            losses[name] = F.cross_entropy(logits, torch.tensor([position], dtype=torch.long))

    total = sum(losses.values())
    return {"total": total, **losses}


def train(
    path: Path,
    out: Path,
    *,
    epochs: int = 4,
    lr: float = 2e-3,
    seed: int = 17,
    emb_dim: int = 64,
    hidden_dim: int = 128,
) -> dict:
    torch.manual_seed(seed)
    dataset = GLLMDataset(path, split="train")
    if not len(dataset):
        raise ValueError("compiler training split is empty")

    model, vocab, relations = build_compiler_from_records(
        dataset.rows,
        emb_dim=emb_dim,
        hidden_dim=hidden_dim,
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    last: dict[str, float] = {}
    global_step = 0

    model.train()
    for epoch in range(epochs):
        for row in dataset.rows:
            losses = compute_example_loss(model, vocab, relations, row)
            optimizer.zero_grad(set_to_none=True)
            losses["total"].backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            global_step += 1
            last = {key: float(value.detach()) for key, value in losses.items()}

    manifest_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    model.save_checkpoint(
        out,
        vocab,
        relations,
        seed=seed,
        manifest_sha=manifest_sha,
        epoch=epochs,
        step=global_step,
    )
    return {
        "examples": len(dataset),
        "epochs": epochs,
        "steps": global_step,
        "seed": seed,
        "manifest_sha": manifest_sha,
        "last_losses": last,
        "checkpoint": str(out),
        "relations": list(relations),
        "vocab_size": len(vocab),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--out", type=Path, default=Path("checkpoints/omega1_1_compiler.pt"))
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-3)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--emb-dim", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=128)
    args = parser.parse_args()
    result = train(
        args.data,
        args.out,
        epochs=args.epochs,
        lr=args.lr,
        seed=args.seed,
        emb_dim=args.emb_dim,
        hidden_dim=args.hidden_dim,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
