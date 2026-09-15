import json
from pathlib import Path

import torch

from training.generate_compiler_corpus import generate_compiler_records
from training.train_compiler import compute_example_loss, build_compiler_from_records


def test_compiler_corpus_has_valid_spans_and_disjoint_template_hashes():
    rows = generate_compiler_records(seed=17, train_count=24, dev_count=12, blind_count=12)
    hashes = {split: set() for split in ("train", "dev", "blind")}
    for row in rows:
        hashes[row["split"]].add(row["template_hash"])
        target = row["compiler_target"]
        if target["relation"] == "abstain":
            assert target["subject_span"] is None
            assert target["object_span"] is None
            continue
        s0, s1 = target["subject_span"]
        o0, o1 = target["object_span"]
        assert row["input_text"][s0:s1] == target["subject_text"]
        assert row["input_text"][o0:o1] == target["object_text"]
    assert hashes["train"].isdisjoint(hashes["dev"])
    assert hashes["train"].isdisjoint(hashes["blind"])
    assert hashes["dev"].isdisjoint(hashes["blind"])


def test_compiler_multitask_loss_is_finite_and_backpropagates():
    rows = generate_compiler_records(seed=3, train_count=8, dev_count=2, blind_count=2)
    train_rows = [r for r in rows if r["split"] == "train"]
    model, vocab, relations = build_compiler_from_records(train_rows, emb_dim=8, hidden_dim=12)
    result = compute_example_loss(model, vocab, relations, train_rows[0])
    assert torch.isfinite(result["total"])
    result["total"].backward()
    assert model.embedding.weight.grad is not None
    assert set(result) >= {"total", "relation", "confidence"}


def test_abstain_example_omits_span_losses():
    rows = generate_compiler_records(seed=5, train_count=20, dev_count=2, blind_count=2)
    train_rows = [r for r in rows if r["split"] == "train"]
    abstain = next(r for r in train_rows if r["compiler_target"]["relation"] == "abstain")
    model, vocab, relations = build_compiler_from_records(train_rows, emb_dim=8, hidden_dim=12)
    losses = compute_example_loss(model, vocab, relations, abstain)
    assert "subject_start" not in losses
    assert "object_start" not in losses
    assert torch.isfinite(losses["total"])
