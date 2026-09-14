import pytest

from nexus_gllm.graph import DynamicHyperGraph
from nexus_gllm.temporal import EventGraphReasoner


def test_before_transitive_closure_and_support():
    graph = DynamicHyperGraph()
    temporal = EventGraphReasoner(graph)
    a = temporal.ensure_event("Дождь начался")
    b = temporal.ensure_event("Ливень усилился")
    c = temporal.ensure_event("Дорогу затопило")
    temporal.add_before(a, b)
    temporal.add_before(b, c)
    result = temporal.before(a, c)
    assert result.holds is True
    assert len(result.support_edge_ids) == 2


def test_after_normalizes_to_reverse_before():
    graph = DynamicHyperGraph()
    temporal = EventGraphReasoner(graph)
    a = temporal.ensure_event("А")
    b = temporal.ensure_event("Б")
    temporal.add_after(b, a)
    assert temporal.before(a, b).holds is True


def test_strict_temporal_cycle_is_rejected():
    graph = DynamicHyperGraph()
    temporal = EventGraphReasoner(graph, strict_dag=True)
    a = temporal.ensure_event("А")
    b = temporal.ensure_event("Б")
    temporal.add_before(a, b)
    with pytest.raises(ValueError, match="cycle"):
        temporal.add_before(b, a)


def test_causal_ancestry_is_transitive():
    graph = DynamicHyperGraph()
    temporal = EventGraphReasoner(graph)
    a = temporal.ensure_event("Ливень усилился")
    b = temporal.ensure_event("Канава переполнилась")
    c = temporal.ensure_event("Дорогу затопило")
    temporal.add_cause(a, b)
    temporal.add_cause(b, c)
    result = temporal.causes(a, c)
    assert result.holds is True
    assert len(result.support_edge_ids) == 2


def test_retracted_edge_is_ignored_by_temporal_queries():
    graph = DynamicHyperGraph()
    temporal = EventGraphReasoner(graph)
    a = temporal.ensure_event("А")
    b = temporal.ensure_event("Б")
    edge = temporal.add_before(a, b)
    assert temporal.before(a, b).holds is True
    graph.retract_edge(edge)
    assert temporal.before(a, b).holds is False
