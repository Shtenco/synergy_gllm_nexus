import torch

from nexus_gllm.realizer_ru import CharVocab, NeuralGraphRealizer, answer_graph_vector
from nexus_gllm.schema import AnswerGraph


def test_neural_realizer_has_bounded_autoregressive_generation():
    vocab = CharVocab.from_texts(["А"])
    model = NeuralGraphRealizer(graph_dim=32, vocab_size=len(vocab), hidden_dim=16, emb_dim=8)
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.zero_()
        model.out.bias[vocab.stoi["А"]] = 10.0

    answer = AnswerGraph(answer_value="А", confidence=1.0, intent="identity")
    text = model.generate(answer_graph_vector(answer, 32), vocab, max_new_tokens=3)
    assert text == "ААА"
