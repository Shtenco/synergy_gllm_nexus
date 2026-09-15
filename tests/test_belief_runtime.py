from nexus_gllm.model import NexusGLLM


def test_conflicting_observations_preserve_both_beliefs_and_project_winner():
    nexus = NexusGLLM()
    first = nexus.observe("Автомобиль принадлежит Антону", source="s1", confidence=0.70, sequence_index=1)
    second = nexus.observe("Автомобиль принадлежит Борису", source="s2", confidence=0.99, sequence_index=2)

    beliefs = nexus.belief("owned_by", "Автомобиль")
    assert len(beliefs) == 2
    assert {b.key.object for b in beliefs} == {"Антон", "Борис"}
    assert any(b.contradiction_set_ids for b in beliefs)
    assert first.gradient_steps == 0
    assert second.gradient_steps == 0

    active = [edge for edge in nexus.graph.find_edges("owned_by") if edge.active]
    assert len(active) == 1
    assert nexus.graph.cards[active[0].targets[0]].label == "Борис"


def test_source_correction_changes_reliability_without_retraining():
    nexus = NexusGLLM()
    before = nexus.correct_source("source-a", was_correct=True, weight=3.0)
    after = nexus.correct_source("source-a", was_correct=False, weight=1.0)
    assert before.reliability > 0.5
    assert 0.0 < after.reliability < 1.0
