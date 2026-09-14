from nexus_gllm.graph import DynamicHyperGraph
from nexus_gllm.schema import GraphCard, NodeType
from nexus_gllm.mutation import StructuralProposal, MutationPolicy


def test_validated_structural_link_can_mutate_graph_but_low_confidence_cannot():
    graph = DynamicHyperGraph()
    graph.add_card(GraphCard(id="a", type=NodeType.PERSON, label="Антон"))
    graph.add_card(GraphCard(id="b", type=NodeType.PERSON, label="Борис"))
    policy = MutationPolicy(threshold=0.8)

    rejected = policy.apply(graph, StructuralProposal(
        op="LINK", source_id="a", target_id="b", relation="knows", confidence=0.5
    ))
    assert rejected.applied is False
    assert graph.find_edges("knows") == []

    accepted = policy.apply(graph, StructuralProposal(
        op="LINK", source_id="a", target_id="b", relation="knows", confidence=0.95
    ))
    assert accepted.applied is True
    assert len(graph.find_edges("knows")) == 1
    assert graph.find_edges("knows")[0].provenance == "neural:validated_proposal"


def test_retract_requires_existing_active_edge():
    graph = DynamicHyperGraph()
    graph.add_card(GraphCard(id="a", type=NodeType.CONCEPT, label="A"))
    graph.add_card(GraphCard(id="b", type=NodeType.CONCEPT, label="B"))
    policy = MutationPolicy(threshold=0.7)
    link = policy.apply(graph, StructuralProposal(op="LINK", source_id="a", target_id="b", relation="r", confidence=1.0))
    edge_id = link.edge_id
    result = policy.apply(graph, StructuralProposal(op="RETRACT", edge_id=edge_id, confidence=0.9))
    assert result.applied is True
    assert graph.edges[edge_id].active is False
