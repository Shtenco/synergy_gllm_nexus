from nexus_gllm.consolidation import GraphConsolidator
from nexus_gllm.graph import DynamicHyperGraph
from nexus_gllm.schema import GraphCard, NodeType, TypedHyperEdge


def test_sleep_merges_duplicate_nodes_and_rewires_edges_without_deletion():
    graph = DynamicHyperGraph()
    graph.add_card(GraphCard(id="a1", type=NodeType.PERSON, label="Антон", provenance="episode:1"))
    graph.add_card(GraphCard(id="a2", type=NodeType.PERSON, label="  антон  ", provenance="episode:2"))
    graph.add_card(GraphCard(id="car", type=NodeType.ENTITY, label="Автомобиль"))
    graph.add_edge(TypedHyperEdge(id="e1", sources=("car",), targets=("a2",), relation="owned_by", confidence=0.7))

    report = GraphConsolidator().run(graph)

    assert report.merged_nodes == 1
    assert graph.cards["a2"].metadata["merged_into"] == "a1"
    assert graph.cards["a2"].metadata["status"] == "merged"
    assert graph.edges["e1"].targets == ("a1",)
    assert "a2" in graph.cards  # no physical deletion


def test_sleep_accumulates_repeated_edge_evidence():
    graph = DynamicHyperGraph()
    graph.add_card(GraphCard(id="x", type=NodeType.ENTITY, label="X"))
    graph.add_card(GraphCard(id="y", type=NodeType.CONCEPT, label="Y"))
    graph.add_edge(TypedHyperEdge(id="e1", sources=("x",), targets=("y",), relation="is_a", confidence=0.6))
    graph.add_edge(TypedHyperEdge(id="e2", sources=("x",), targets=("y",), relation="is_a", confidence=0.5))

    report = GraphConsolidator().run(graph)

    active = [e for e in graph.find_edges("is_a")]
    assert len(active) == 1
    assert abs(active[0].confidence - 0.8) < 1e-9
    assert active[0].provenance == "sleep:semantic"
    assert active[0].consolidation_strength > 0
    assert report.merged_edges == 1


def test_sleep_keeps_only_best_supported_exclusive_state_active():
    graph = DynamicHyperGraph()
    graph.add_card(GraphCard(id="car", type=NodeType.ENTITY, label="Автомобиль"))
    graph.add_card(GraphCard(id="a", type=NodeType.PERSON, label="Антон"))
    graph.add_card(GraphCard(id="b", type=NodeType.PERSON, label="Борис"))
    graph.add_edge(TypedHyperEdge(id="old", sources=("car",), targets=("a",), relation="owned_by", confidence=0.7))
    graph.add_edge(TypedHyperEdge(id="new", sources=("car",), targets=("b",), relation="owned_by", confidence=0.95))

    report = GraphConsolidator().run(graph)

    assert graph.edges["new"].active is True
    assert graph.edges["old"].active is False
    assert graph.edges["old"].metadata["sleep_retracted"] is True
    assert report.retracted_conflicts == 1


def test_sleep_strengthens_repeated_cards_and_retains_protected_fact():
    graph = DynamicHyperGraph()
    graph.add_card(GraphCard(
        id="fact", type=NodeType.CLAIM, label="2+2=4", confidence=1.0,
        provenance="authority", metadata={"protected": True, "evidence_count": 3}
    ))
    report = GraphConsolidator().run(graph)
    assert "fact" in graph.cards
    assert graph.cards["fact"].confidence == 1.0
    assert graph.cards["fact"].consolidation_strength > 0
    assert report.protected_retained == 1
