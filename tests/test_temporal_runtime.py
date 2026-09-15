from nexus_gllm.model import NexusGLLM


def test_nexus_asks_which_event_was_earlier():
    nexus = NexusGLLM()
    nexus.learn("Сначала дождь начался, потом дорогу затопило.")
    response = nexus.ask("Что было раньше: дождь начался или дорогу затопило?")
    assert response.answer_graph.answer_value == "дождь начался"
    assert response.answer_graph.intent == "temporal_choice"
    assert response.confidence == 1.0


def test_nexus_asks_for_direct_or_ancestral_cause():
    nexus = NexusGLLM()
    nexus.learn("Ливень усилился, поэтому канава переполнилась.")
    nexus.learn("Канава переполнилась, поэтому дорогу затопило.")
    response = nexus.ask("Что стало причиной дорогу затопило?")
    assert response.answer_graph.answer_value in {"Канава переполнилась", "Ливень усилился"}
    assert response.answer_graph.intent == "cause_of"
    assert response.confidence > 0


def test_sleep_is_public_and_returns_consolidation_report():
    nexus = NexusGLLM()
    nexus.learn("Автомобиль принадлежит Антону")
    report = nexus.sleep()
    assert report.merged_nodes >= 0
    assert report.protected_retained >= 0
