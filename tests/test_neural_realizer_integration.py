from pathlib import Path

import torch

from nexus_gllm.model import NexusGLLM
from nexus_gllm.realizer_ru import CharVocab, NeuralGraphRealizer


def test_nexus_can_load_native_realizer_but_falls_back_if_semantics_are_not_preserved(tmp_path: Path):
    vocab = CharVocab.from_texts(["Х"])
    realizer = NeuralGraphRealizer(graph_dim=32, vocab_size=len(vocab), hidden_dim=16, emb_dim=8)
    with torch.no_grad():
        for p in realizer.parameters():
            p.zero_()
        realizer.out.bias[vocab.stoi["Х"]] = 10.0
    ckpt = tmp_path / "realizer.pt"
    realizer.save_checkpoint(ckpt, vocab)

    model = NexusGLLM()
    model.load_realizer_checkpoint(ckpt)
    model.learn("Антон старше Бориса")
    model.learn("Борис старше Виктора")
    response = model.ask("Кто самый старший?", prefer_neural_realizer=True)

    assert response.text == "Самый старший — Антон."
    assert response.realizer_mode == "deterministic_fallback"
