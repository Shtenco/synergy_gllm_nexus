import torch

from training.generate_compiler_corpus import generate_compiler_records
from training.train_compiler import batch_loss, build_compiler_from_records, evaluate_records


def test_batch_loss_handles_mixed_abstain_and_structured_examples():
    rows = generate_compiler_records(seed=17, train_count=32, dev_count=8, blind_count=8)
    train_rows = [row for row in rows if row["split"] == "train"]
    model, vocab, relations = build_compiler_from_records(train_rows, emb_dim=8, hidden_dim=12)
    losses = batch_loss(model, vocab, relations, train_rows[:16])
    assert torch.isfinite(losses["total"])
    assert set(losses) >= {"total", "relation", "confidence", "span"}
    losses["total"].backward()
    assert model.embedding.weight.grad is not None


def test_dev_evaluation_reports_loss_and_relation_accuracy():
    rows = generate_compiler_records(seed=18, train_count=16, dev_count=8, blind_count=8)
    train_rows = [row for row in rows if row["split"] == "train"]
    dev_rows = [row for row in rows if row["split"] == "dev"]
    model, vocab, relations = build_compiler_from_records(train_rows, emb_dim=8, hidden_dim=12)
    metrics = evaluate_records(model, vocab, relations, dev_rows, batch_size=4)
    assert metrics["examples"] == len(dev_rows)
    assert metrics["loss"] >= 0
    assert 0.0 <= metrics["relation_accuracy"] <= 1.0
