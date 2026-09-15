from nexus_gllm.model import NexusGLLM


def test_new_exclusive_world_fact_retracts_old_ownership():
    model = NexusGLLM()
    model.learn("Автомобиль принадлежит Антону")
    assert model.ask("Кому принадлежит Автомобиль?").answer_graph.answer_value == "Антон"

    model.learn("Автомобиль принадлежит Борису")
    response = model.ask("Кому принадлежит Автомобиль?")
    assert response.answer_graph.answer_value == "Борис"

    active = [e for e in model.graph.find_edges("owned_by") if e.sources[0] in response.answer_graph.support_node_ids]
    assert len(active) == 1
    assert any(not e.active for e in model.graph.edges.values() if e.relation == "owned_by")
