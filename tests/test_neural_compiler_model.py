from pathlib import Path

import torch

from nexus_gllm.compiler_neural import CompilerCharVocab, NeuralRussianGraphCompiler


def test_compiler_forward_shapes_and_gradients():
    texts = ["Антон старше Бориса", "Москва находится в России"]
    vocab = CompilerCharVocab.from_texts(texts)
    model = NeuralRussianGraphCompiler(
        vocab_size=len(vocab),
        relation_count=5,
        emb_dim=16,
        hidden_dim=24,
    )
    encoded, mask = vocab.batch_encode(texts)
    out = model(encoded, mask)
    assert out["relation_logits"].shape == (2, 5)
    assert out["subject_start_logits"].shape == encoded.shape
    assert out["subject_end_logits"].shape == encoded.shape
    assert out["object_start_logits"].shape == encoded.shape
    assert out["object_end_logits"].shape == encoded.shape
    assert out["confidence_logit"].shape == (2,)
    sum(v.sum() for v in out.values()).backward()
    assert model.embedding.weight.grad is not None


def test_compiler_predict_decodes_bounded_spans():
    text = "Антон старше Бориса"
    vocab = CompilerCharVocab.from_texts([text])
    model = NeuralRussianGraphCompiler(
        vocab_size=len(vocab),
        relation_count=2,
        emb_dim=8,
        hidden_dim=12,
    )
    # Force a deterministic prediction through head biases.
    with torch.no_grad():
        for p in model.parameters():
            p.zero_()
        model.relation_head.bias[0] = 10.0
        model.confidence_head.bias.fill_(10.0)
        model.subject_start_head.bias.fill_(0.0)
        model.subject_end_head.bias.fill_(0.0)
        model.object_start_head.bias.fill_(0.0)
        model.object_end_head.bias.fill_(0.0)
    proposal = model.predict(text, vocab, relations=("older_than", "abstain"))
    assert proposal.relation == "older_than"
    assert 0 <= proposal.subject_span[0] < proposal.subject_span[1] <= len(text)
    assert 0 <= proposal.object_span[0] < proposal.object_span[1] <= len(text)
    assert 0.0 <= proposal.confidence <= 1.0


def test_compiler_checkpoint_round_trip(tmp_path: Path):
    vocab = CompilerCharVocab.from_texts(["Антон старше Бориса"])
    relations = ("older_than", "abstain")
    model = NeuralRussianGraphCompiler(
        vocab_size=len(vocab),
        relation_count=len(relations),
        emb_dim=8,
        hidden_dim=12,
    )
    path = tmp_path / "compiler.pt"
    model.save_checkpoint(path, vocab, relations, seed=17, manifest_sha="abc")
    loaded, loaded_vocab, loaded_relations, meta = NeuralRussianGraphCompiler.load_checkpoint(path)
    assert loaded_relations == relations
    assert loaded_vocab.tokens == vocab.tokens
    assert meta["manifest_sha"] == "abc"
    assert meta["seed"] == 17
    for key, value in model.state_dict().items():
        assert torch.equal(value, loaded.state_dict()[key])
