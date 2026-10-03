from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1, CognitiveRequest
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, TaskOpcode, TaskProgram, WorldFact, WorldHypothesis


def _request(program: ProgramNode) -> CognitiveRequest:
    op = OperatorSymbol("r", 2)
    world = WorldHypothesis(
        "proof-dag-world",
        (
            WorldFact(op, (Entity("a"), Entity("b"))),
            WorldFact(op, (Entity("b"), Entity("c"))),
        ),
    )
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "r", ("a", "c"))
    return CognitiveRequest(
        episode_id="proof-dag-episode",
        world=world,
        task=task,
        program=program,
        novelty=0.2,
        uncertainty=0.2,
        memory_tags=(),
        planning_state=None,
    )


def test_composed_program_exposes_dependency_nodes_and_multistep_state():
    left = ProgramNode(
        ProgramKind.ATOM,
        "rule:transitive:r",
        params=(("step", "left"),),
    )
    right = ProgramNode(
        ProgramKind.ATOM,
        "rule:transitive:r",
        params=(("step", "right"),),
    )
    root = ProgramNode(ProgramKind.COMPOSE, children=(left, right))

    decision = CognitiveLoopR1().deliberate(_request(root))

    root_id = "program:" + root.program_id
    left_id = "program:" + left.program_id
    right_id = "program:" + right.program_id

    assert {root_id, left_id, right_id}.issubset(decision.trace_graph.nodes)
    assert decision.trace_graph.nodes[root_id].payload["ast_kind"] == ProgramKind.COMPOSE.value
    assert decision.trace_graph.nodes[left_id].payload["ast_kind"] == ProgramKind.ATOM.value
    assert decision.trace_graph.nodes[right_id].payload["ast_kind"] == ProgramKind.ATOM.value

    edges = {(edge.parent_id, edge.child_id) for edge in decision.trace_graph.edges}
    assert (left_id, root_id) in edges
    assert (right_id, root_id) in edges
    assert (root_id, "answer") in edges

    assert set(decision.state.program_ids) == {root.program_id, left.program_id, right.program_id}
