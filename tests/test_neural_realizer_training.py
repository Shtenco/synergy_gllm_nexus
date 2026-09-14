from pathlib import Path

import torch

from nexus_gllm.realizer_ru import CharVocab, NeuralGraphRealizer, answer_graph_vector
from nexus_gllm.schema import AnswerGraph


def test_char_vocab_roundtrip_and_answer_graph_vector_is_deterministic():
    vocab = CharVocab.from_texts(["Самый старший — Антон.", "Принадлежит: Борис."])
    text = "Самый старший — Антон."
    assert vocab.decode(vocab.encode(text)) == text

    answer = AnswerGraph(answer_value="Антон", confidence=1.0, intent="oldest")
    a = answer_graph_vector(answer, dim=32)
    b = answer_graph_vector(answer, dim=32)
    assert a.shape == (32,)
    assert torch.equal(a, b)


def test_neural_realizer_checkpoint_roundtrip(tmp_path: Path):
    vocab = CharVocab.from_texts(["Ответ: Антон."])
    model = NeuralGraphRealizer(graph_dim=32, vocab_size=len(vocab), hidden_dim=24, emb_dim=12)
    path = tmp_path / "realizer.pt"
    model.save_checkpoint(path, vocab)

    loaded, loaded_vocab = NeuralGraphRealizer.load_checkpoint(path)
    assert loaded_vocab.tokens == vocab.tokens
    for left, right in zip(model.parameters(), loaded.parameters()):
        assert torch.equal(left, right)
