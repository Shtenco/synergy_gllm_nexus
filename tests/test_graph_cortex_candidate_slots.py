import torch

from nexus_gllm.graph_cortex import GraphConstructionCortex
from training.graph_cortex_dataset import CandidateVocab, enumerate_candidates


def test_gold_spans_are_candidate_spans():
    text = "Владельцем dev_объект_000982 является dev_A_000982"
    spans = set(enumerate_candidates(text, max_words=2))
    assert (11, 28) in spans
    assert (38, 50) in spans


def test_graph_cortex_outputs_role_and_relation_logits_with_gradients():
    vocab = CandidateVocab.from_texts(["tr_объект_1 принадлежит tr_A_1"])
    model = GraphConstructionCortex(
        len(vocab), relation_count=7, char_dim=24, hidden=32, slot_dim=64
    )
    batch = vocab.batch_encode(["tr_объект_1 принадлежит tr_A_1"], max_len=64)
    candidates = torch.tensor([[[0, 11], [23, 29], [0, 29], [-1, -1]]])
    candidate_mask = torch.tensor([[True, True, True, False]])
    output = model(
        batch["tokens"], batch["mask"], batch["morph"], candidates, candidate_mask
    )
    assert output["relation_logits"].shape == (1, 7)
    assert output["subject_candidate_logits"].shape == (1, 4)
    assert output["object_candidate_logits"].shape == (1, 4)
    loss = (
        output["relation_logits"].sum()
        + output["subject_candidate_logits"][:, :3].sum()
        + output["object_candidate_logits"][:, :3].sum()
    )
    loss.backward()
    assert any(
        parameter.grad is not None and torch.isfinite(parameter.grad).all()
        for parameter in model.parameters()
    )


def test_prefix_candidate_pool_matches_naive_span_means():
    model = GraphConstructionCortex(10, 7, char_dim=8, hidden=8, slot_dim=16)
    encoded = torch.arange(1 * 6 * 4, dtype=torch.float32).reshape(1, 6, 4)
    candidates = torch.tensor([[[0, 2], [2, 5], [-1, -1]]])
    candidate_mask = torch.tensor([[True, True, False]])
    pooled = model._candidate_pool_prefix(encoded, candidates, candidate_mask)
    assert torch.allclose(pooled[0, 0], encoded[0, 0:2].mean(0))
    assert torch.allclose(pooled[0, 1], encoded[0, 2:5].mean(0))
    assert torch.all(pooled[0, 2] == 0)
