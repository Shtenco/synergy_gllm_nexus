from nexus_gllm.model import NexusGLLM


def test_end_to_end_response_contains_recurrent_graph_cognition_without_changing_answer():
    model = NexusGLLM(neural_seed=17)
    model.learn("Антон старше Бориса")
    model.learn("Борис старше Виктора")

    response = model.ask("Кто самый старший?")
    assert response.answer_graph.answer_value == "Антон"
    assert len(response.cognition_logits) == 6
    assert response.cognition_steps == 3

    second = model.ask("Кто самый старший?")
    assert second.cognition_logits == response.cognition_logits
    assert second.text == "Самый старший — Антон."
