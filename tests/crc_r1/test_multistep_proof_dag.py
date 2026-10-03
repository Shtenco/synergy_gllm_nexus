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


def _request_with_world(program: ProgramNode, world: WorldHypothesis, task: TaskProgram) -> CognitiveRequest:
    return CognitiveRequest(
        episode_id="proof-dag-control-episode",
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


def test_program_dag_nodes_carry_verified_execution_evidence():
    left = ProgramNode(ProgramKind.ATOM, "rule:transitive:r", params=(("step", "left"),))
    right = ProgramNode(ProgramKind.ATOM, "rule:transitive:r", params=(("step", "right"),))
    root = ProgramNode(ProgramKind.COMPOSE, children=(left, right))

    decision = CognitiveLoopR1().deliberate(_request(root))

    by_id = {step.program_id: step for step in decision.execution.steps}
    assert set(by_id) == {root.program_id, left.program_id, right.program_id}
    assert by_id[left.program_id].execution.truth is True
    assert by_id[right.program_id].execution.truth is True
    assert by_id[root.program_id].execution.truth is True
    assert by_id[left.program_id].evidence_kind == "PROOF"
    assert by_id[right.program_id].evidence_kind == "PROOF"
    assert by_id[root.program_id].evidence_kind == "DETERMINISTIC"

    for node in (root, left, right):
        payload = decision.trace_graph.nodes["program:" + node.program_id].payload
        assert payload["status"] == "EXECUTED"
        assert payload["truth"] is True
        assert payload["world_id"] == "proof-dag-world"
        assert payload["evidence_kind"] in {"PROOF", "DETERMINISTIC"}
        assert payload["verified"] is True


def test_if_false_excludes_unexecuted_body_from_proof_dag_and_state():
    guard = OperatorSymbol("guard", 2)
    relation = OperatorSymbol("r", 2)
    world = WorldHypothesis(
        "proof-dag-if-world",
        (
            WorldFact(guard, (Entity("x"), Entity("y")), False),
            WorldFact(relation, (Entity("a"), Entity("b"))),
            WorldFact(relation, (Entity("b"), Entity("c"))),
        ),
    )
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "r", ("a", "c"))
    condition = ProgramNode(
        ProgramKind.ATOM,
        "rule:transitive:guard",
        params=(("query_operator", "guard"), ("query_src", "x"), ("query_dst", "y")),
    )
    body = ProgramNode(ProgramKind.ATOM, "rule:transitive:r")
    root = ProgramNode(ProgramKind.IF, children=(condition, body))

    decision = CognitiveLoopR1().deliberate(_request_with_world(root, world, task))

    root_id = "program:" + root.program_id
    condition_id = "program:" + condition.program_id
    body_id = "program:" + body.program_id

    assert root_id in decision.trace_graph.nodes
    assert condition_id in decision.trace_graph.nodes
    assert body_id not in decision.trace_graph.nodes
    assert body.program_id not in decision.state.program_ids
    assert set(decision.state.program_ids) == {root.program_id, condition.program_id}

    edges = {(edge.parent_id, edge.child_id) for edge in decision.trace_graph.edges}
    assert (condition_id, root_id) in edges
    assert (body_id, root_id) not in edges

    root_payload = decision.trace_graph.nodes[root_id].payload
    condition_payload = decision.trace_graph.nodes[condition_id].payload
    assert root_payload["status"] == "CONDITION_FALSE"
    assert root_payload["truth"] is False
    assert root_payload["evidence_kind"] == "DETERMINISTIC"
    assert root_payload["verified"] is True
    assert condition_payload["status"] == "EXECUTED"
    assert condition_payload["truth"] is False
    assert condition_payload["evidence_kind"] == "PROOF"
    assert condition_payload["verified"] is True


def test_proof_coverage_certificate_rejects_unresolved_dependency():
    proved = ProgramNode(ProgramKind.ATOM, "rule:transitive:r", params=(("step", "proved"),))
    unresolved = ProgramNode(
        ProgramKind.ATOM,
        "rule:transitive:r",
        params=(("query_operator", "r"), ("query_src", "a"), ("query_dst", "z")),
    )
    root = ProgramNode(ProgramKind.COMPOSE, children=(proved, unresolved))

    decision = CognitiveLoopR1().deliberate(_request(root))
    coverage = decision.execution.proof_coverage

    assert coverage.required_node_ids == (proved.program_id, unresolved.program_id, root.program_id)
    assert coverage.verified_node_ids == (proved.program_id,)
    assert coverage.unverified_node_ids == (unresolved.program_id, root.program_id)
    assert coverage.coverage == 1 / 3
    assert coverage.complete is False
    assert decision.trace_graph.nodes["answer"].payload["proof_complete"] is False
    assert decision.trace_graph.nodes["answer"].payload["proof_coverage"] == 1 / 3


def test_proof_coverage_certificate_is_complete_for_verified_composition():
    left = ProgramNode(ProgramKind.ATOM, "rule:transitive:r", params=(("step", "left"),))
    right = ProgramNode(ProgramKind.ATOM, "rule:transitive:r", params=(("step", "right"),))
    root = ProgramNode(ProgramKind.COMPOSE, children=(left, right))

    decision = CognitiveLoopR1().deliberate(_request(root))
    coverage = decision.execution.proof_coverage

    assert coverage.required_node_ids == (left.program_id, right.program_id, root.program_id)
    assert coverage.unverified_node_ids == ()
    assert coverage.coverage == 1.0
    assert coverage.complete is True
    assert decision.trace_graph.nodes["answer"].payload["proof_complete"] is True
    assert decision.trace_graph.nodes["answer"].payload["proof_coverage"] == 1.0
