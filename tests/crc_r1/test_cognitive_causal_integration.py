from nexus_gllm.unified_v3.cognitive.causal_model import (
    CausalEvidence,
    CausalEvidenceKind,
)
from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1, CognitiveRequest
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.contracts import (
    Entity,
    OperatorSymbol,
    TaskOpcode,
    TaskProgram,
    WorldFact,
    WorldHypothesis,
)


def _base_request(*, causal_evidence):
    relation = OperatorSymbol("r", 2)
    world = WorldHypothesis(
        "causal-loop-world",
        (
            WorldFact(relation, (Entity("a"), Entity("b"))),
            WorldFact(relation, (Entity("b"), Entity("c"))),
        ),
    )
    return CognitiveRequest(
        episode_id="causal-loop-episode",
        world=world,
        task=TaskProgram(TaskOpcode.QUERY_RELATION, "r", ("a", "c")),
        program=ProgramNode(ProgramKind.ATOM, "rule:transitive:r"),
        causal_query=("x", "y"),
        causal_evidence=tuple(causal_evidence),
        novelty=0.2,
        uncertainty=0.2,
    )


def test_interventional_plus_counterfactual_evidence_opens_causal_answer_gate():
    evidence = (
        CausalEvidence("i", "x", "y", CausalEvidenceKind.INTERVENTIONAL, 0.9, 0.95),
        CausalEvidence("cf", "x", "y", CausalEvidenceKind.COUNTERFACTUAL, 0.8, 0.9),
    )

    decision = CognitiveLoopR1().deliberate(_base_request(causal_evidence=evidence))

    assert decision.execution.execution.truth is True
    assert decision.causal_edge is not None
    assert decision.causal_edge.identified is True
    assert decision.answer is True

    causal_id = "causal:x->y"
    assert causal_id in decision.trace_graph.nodes
    payload = decision.trace_graph.nodes[causal_id].payload
    assert payload["identified"] is True
    assert payload["interventional_mass"] > 0
    assert payload["counterfactual_mass"] > 0

    answer_payload = decision.trace_graph.nodes["answer"].payload
    assert answer_payload["causal_gate_required"] is True
    assert answer_payload["causal_gate_open"] is True
    edges = {(edge.parent_id, edge.child_id) for edge in decision.trace_graph.edges}
    assert (causal_id, "answer") in edges

    causal_events = [event for event in decision.state.trace if event.kind == "causal_inference"]
    assert len(causal_events) == 1


def test_observational_correlation_alone_fail_closes_causal_answer_gate():
    evidence = (
        CausalEvidence("o", "x", "y", CausalEvidenceKind.OBSERVATIONAL, 1.0, 0.99),
    )

    decision = CognitiveLoopR1().deliberate(_base_request(causal_evidence=evidence))

    # The symbolic program itself proves the queried relation. The causal gate
    # still must abstain because correlation alone does not identify x -> y.
    assert decision.execution.execution.truth is True
    assert decision.causal_edge is not None
    assert decision.causal_edge.identified is False
    assert decision.answer is None

    causal_id = "causal:x->y"
    payload = decision.trace_graph.nodes[causal_id].payload
    assert payload["identified"] is False
    assert payload["observational_mass"] > 0
    assert payload["interventional_mass"] == 0

    answer_payload = decision.trace_graph.nodes["answer"].payload
    assert answer_payload["causal_gate_required"] is True
    assert answer_payload["causal_gate_open"] is False
    edges = {(edge.parent_id, edge.child_id) for edge in decision.trace_graph.edges}
    assert (causal_id, "answer") in edges
