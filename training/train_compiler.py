from __future__ import annotations

import argparse
import hashlib
import json
import random
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

    device = next(model.parameters()).device
    tokens, mask = vocab.batch_encode([text])
    tokens, mask = tokens.to(device), mask.to(device)
    out = model(tokens, mask)
    relation_target = torch.tensor([relations.index(relation)], dtype=torch.long, device=device)
    confidence_target = torch.tensor([float(target.get("confidence", 1.0))], dtype=torch.float32, device=device)

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
            losses[name] = F.cross_entropy(
                logits,
                torch.tensor([position], dtype=torch.long, device=device),
            )

    total = sum(losses.values())
    return {"total": total, **losses}


def batch_loss(
    model: NeuralRussianGraphCompiler,
    vocab: CompilerCharVocab,
    relations: tuple[str, ...],
    rows: list[dict],
) -> dict[str, torch.Tensor]:
    if not rows:
        raise ValueError("batch must be non-empty")
    device = next(model.parameters()).device
    texts = [row["input_text"] for row in rows]
    tokens, mask = vocab.batch_encode(texts)
    tokens, mask = tokens.to(device), mask.to(device)
    out = model(tokens, mask)

    relation_targets = torch.tensor(
        [relations.index(row["compiler_target"]["relation"]) for row in rows],
        dtype=torch.long,
        device=device,
    )
    confidence_targets = torch.tensor(
        [float(row["compiler_target"].get("confidence", 1.0)) for row in rows],
        dtype=torch.float32,
        device=device,
    )
    relation_loss = F.cross_entropy(out["relation_logits"], relation_targets)
    confidence_loss = F.binary_cross_entropy_with_logits(out["confidence_logit"], confidence_targets)

    structured_indices = [
        i for i, row in enumerate(rows)
        if row["compiler_target"]["relation"] != "abstain"
    ]
    if structured_indices:
        index = torch.tensor(structured_indices, dtype=torch.long, device=device)
        target_positions = {
            "subject_start": [],
            "subject_end": [],
            "object_start": [],
            "object_end": [],
        }
        for i in structured_indices:
            target = rows[i]["compiler_target"]
            subject_span = target["subject_span"]
            object_span = target["object_span"]
            if subject_span is None or object_span is None:
                raise ValueError("non-abstain target requires spans")
            target_positions["subject_start"].append(int(subject_span[0]))
            target_positions["subject_end"].append(int(subject_span[1]) - 1)
            target_positions["object_start"].append(int(object_span[0]))
            target_positions["object_end"].append(int(object_span[1]) - 1)

        span_components = []
        for name, positions in target_positions.items():
            logits = out[f"{name}_logits"].index_select(0, index)
            target_tensor = torch.tensor(positions, dtype=torch.long, device=device)
            if int(target_tensor.max()) >= logits.shape[1] or int(target_tensor.min()) < 0:
                raise ValueError(f"{name} target out of bounds")
            span_components.append(F.cross_entropy(logits, target_tensor))
        span_loss = torch.stack(span_components).mean()
    else:
        span_loss = relation_loss.new_zeros(())

    total = relation_loss + confidence_loss + span_loss
    return {
        "total": total,
        "relation": relation_loss,
        "confidence": confidence_loss,
        "span": span_loss,
    }


def _batches(rows: list[dict], batch_size: int):
    for start in range(0, len(rows), batch_size):
        yield rows[start : start + batch_size]


def evaluate_records(
    model: NeuralRussianGraphCompiler,
    vocab: CompilerCharVocab,
    relations: tuple[str, ...],
    rows: list[dict],
    *,
    batch_size: int = 64,
) -> dict:
    if not rows:
        return {"examples": 0, "loss": 0.0, "relation_accuracy": 0.0}
    was_training = model.training
    model.eval()
    total_loss = 0.0
    total_examples = 0
    relation_correct = 0
    device = next(model.parameters()).device
    with torch.no_grad():
        for batch in _batches(rows, batch_size):
            losses = batch_loss(model, vocab, relations, batch)
            total_loss += float(losses["total"]) * len(batch)
            texts = [row["input_text"] for row in batch]
            tokens, mask = vocab.batch_encode(texts)
            out = model(tokens.to(device), mask.to(device))
            predicted = out["relation_logits"].argmax(-1).cpu().tolist()
            gold = [relations.index(row["compiler_target"]["relation"]) for row in batch]
            relation_correct += sum(int(p == g) for p, g in zip(predicted, gold))
            total_examples += len(batch)
    if was_training:
        model.train()
    return {
        "examples": total_examples,
        "loss": total_loss / total_examples,
        "relation_accuracy": relation_correct / total_examples,
    }


def _resolve_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(requested)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA requested but unavailable")
    return device


def train(
    path: Path,
    out: Path,
    *,
    epochs: int = 4,
    lr: float = 2e-3,
    seed: int = 17,
    emb_dim: int = 64,
    hidden_dim: int = 128,
    batch_size: int = 64,
    device: str = "auto",
) -> dict:
    torch.manual_seed(seed)
    train_dataset = GLLMDataset(path, split="train")
    dev_dataset = GLLMDataset(path, split="dev")
    if not len(train_dataset):
        raise ValueError("compiler training split is empty")
    if batch_size < 1:
        raise ValueError("batch_size must be >=1")

    model, vocab, relations = build_compiler_from_records(
        train_dataset.rows,
        emb_dim=emb_dim,
        hidden_dim=hidden_dim,
    )
    runtime_device = _resolve_device(device)
    model.to(runtime_device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    global_step = 0
    manifest_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    history: list[dict] = []
    best_dev_loss = float("inf")
    best_epoch = 0
    rng = random.Random(seed)

    for epoch in range(1, epochs + 1):
        rows = list(train_dataset.rows)
        rng.shuffle(rows)
        model.train()
        running_loss = 0.0
        seen = 0
        for batch in _batches(rows, batch_size):
            losses = batch_loss(model, vocab, relations, batch)
            optimizer.zero_grad(set_to_none=True)
            losses["total"].backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            global_step += 1
            running_loss += float(losses["total"].detach()) * len(batch)
            seen += len(batch)

        train_loss = running_loss / max(1, seen)
        dev_metrics = evaluate_records(
            model,
            vocab,
            relations,
            dev_dataset.rows,
            batch_size=batch_size,
        ) if len(dev_dataset) else {"examples": 0, "loss": train_loss, "relation_accuracy": 0.0}
        epoch_record = {
            "epoch": epoch,
            "train_loss": train_loss,
            "dev_loss": dev_metrics["loss"],
            "dev_relation_accuracy": dev_metrics["relation_accuracy"],
        }
        history.append(epoch_record)

        if dev_metrics["loss"] < best_dev_loss:
            best_dev_loss = dev_metrics["loss"]
            best_epoch = epoch
            model.save_checkpoint(
                out,
                vocab,
                relations,
                seed=seed,
                manifest_sha=manifest_sha,
                epoch=epoch,
                step=global_step,
            )

    return {
        "train_examples": len(train_dataset),
        "dev_examples": len(dev_dataset),
        "epochs": epochs,
        "steps": global_step,
        "batch_size": batch_size,
        "device": str(runtime_device),
        "seed": seed,
        "manifest_sha": manifest_sha,
        "best_epoch": best_epoch,
        "best_dev_loss": best_dev_loss,
        "history": history,
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
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    result = train(
        args.data,
        args.out,
        epochs=args.epochs,
        lr=args.lr,
        seed=args.seed,
        emb_dim=args.emb_dim,
        hidden_dim=args.hidden_dim,
        batch_size=args.batch_size,
        device=args.device,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
