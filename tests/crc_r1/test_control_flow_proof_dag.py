from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1, CognitiveRequest
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, TaskOpcode, TaskProgram, WorldFact, WorldHypothesis
from nexus_gllm.unified_v3.temporal import TemporalLedger


def _atom(symbol: str, *, operator: str | None = None, src: str | None = None, dst: str | None = None) -> ProgramNode:
    params = ()
    if operator is not None:
        params = (("query_operator", operator), ("query_src", src), ("query_dst", dst))
    return ProgramNode(ProgramKind.ATOM, symbol, params=params)


def _request(program: ProgramNode, world: WorldHypothesis, task: TaskProgram, *, ledger: TemporalLedger | None = None) -> CognitiveRequest:
    return CognitiveRequest(
        episode_id="control-flow-proof-dag",
        world=world,
        task=task,
        program=program,
        temporal_ledger=ledger,
        novelty=0.2,
        uncertainty=0.2,
    )


def _graph_id(decision, step_path: tuple[int, ...]) -> str:
    step = next(step for step in decision.execution.steps if step.step_path == step_path)
    return "program:" + decision.execution.step_identity(step)


def test_temporal_proof_dag_records_snapshot_world_on_root_and_executed_child():
    ledger = (
        TemporalLedger()
        .assert_fact("state", "node", "old", 1)
        .assert_fact("state", "node", "new", 10, supersede=True)
    )
    world = WorldHypothesis("temporal-proof-world", ())
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "state", ("node", "old"))
    child = _atom("rule:transitive:state", operator="state", src="node", dst="old")
    root = ProgramNode(ProgramKind.TEMPORAL, children=(child,), params=(("time", "5"),))

    decision = CognitiveLoopR1().deliberate(_request(root, world, task, ledger=ledger))

    root_id = _graph_id(decision, ())
    child_id = _graph_id(decision, (0,))
    expected_world = "temporal-proof-world:temporal:at:5"

    assert set(decision.state.program_ids) == {root.program_id, child.program_id}
    assert decision.trace_graph.nodes[root_id].payload["world_id"] == expected_world
    assert decision.trace_graph.nodes[child_id].payload["world_id"] == expected_world
    assert decision.trace_graph.nodes[root_id].payload["status"] == "EXECUTED"
    assert decision.trace_graph.nodes[child_id].payload["status"] == "EXECUTED"
    assert decision.trace_graph.nodes[root_id].payload["verified"] is True
    assert decision.trace_graph.nodes[child_id].payload["verified"] is True
    assert (child_id, root_id) in {(edge.parent_id, edge.child_id) for edge in decision.trace_graph.edges}
    assert decision.execution.proof_coverage.complete is True


def test_inhibit_blocked_body_is_absent_from_executed_proof_dag_and_state():
    block = OperatorSymbol("block", 2)
    relation = OperatorSymbol("r", 2)
    world = WorldHypothesis(
        "inhibit-proof-world",
        (
            WorldFact(block, (Entity("x"), Entity("y")), True),
            WorldFact(relation, (Entity("a"), Entity("b")), True),
            WorldFact(relation, (Entity("b"), Entity("c")), True),
        ),
    )
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "r", ("a", "c"))
    blocker = _atom("rule:transitive:block", operator="block", src="x", dst="y")
    body = _atom("rule:transitive:r")
    root = ProgramNode(ProgramKind.INHIBIT, children=(blocker, body))

    decision = CognitiveLoopR1().deliberate(_request(root, world, task))

    root_id = _graph_id(decision, ())
    blocker_id = _graph_id(decision, (0,))
    body_prefix = "program:" + body.program_id

    assert set(decision.state.program_ids) == {root.program_id, blocker.program_id}
    assert body.program_id not in decision.state.program_ids
    assert all(not node_id.startswith(body_prefix) for node_id in decision.trace_graph.nodes)
    assert decision.trace_graph.nodes[root_id].payload["status"] == "INHIBITED"
    assert decision.trace_graph.nodes[root_id].payload["truth"] is None
    assert decision.trace_graph.nodes[root_id].payload["evidence_kind"] == "DETERMINISTIC"
    assert decision.trace_graph.nodes[root_id].payload["verified"] is True
    assert decision.trace_graph.nodes[blocker_id].payload["truth"] is True
    assert decision.trace_graph.nodes[blocker_id].payload["evidence_kind"] == "PROOF"
    assert (blocker_id, root_id) in {(edge.parent_id, edge.child_id) for edge in decision.trace_graph.edges}
    assert decision.execution.proof_coverage.complete is True


def test_nested_compose_preserves_temporal_counterfactual_and_inhibit_dependencies():
    relation = OperatorSymbol("r", 2)
    blocker = OperatorSymbol("block", 2)
    world = WorldHypothesis(
        "nested-proof-world",
        (
            WorldFact(relation, (Entity("a"), Entity("b")), True),
            WorldFact(relation, (Entity("b"), Entity("c")), True),
            WorldFact(blocker, (Entity("x"), Entity("y")), False),
        ),
    )
    ledger = TemporalLedger().assert_fact("state", "node", "ready", 3)
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "r", ("a", "c"))

    temporal_atom = _atom("rule:transitive:state", operator="state", src="node", dst="ready")
    temporal = ProgramNode(ProgramKind.TEMPORAL, children=(temporal_atom,), params=(("mode", "current"),))

    cf_atom = _atom("rule:transitive:r", operator="r", src="a", dst="d")
    counterfactual = ProgramNode(
        ProgramKind.COUNTERFACTUAL,
        children=(cf_atom,),
        params=(("kind", "ADD_FACT"), ("operator", "r"), ("src", "c"), ("dst", "d")),
    )

    inhibit_blocker = _atom("rule:transitive:block", operator="block", src="x", dst="y")
    inhibit_body = _atom("rule:transitive:r", operator="r", src="a", dst="c")
    inhibit = ProgramNode(ProgramKind.INHIBIT, children=(inhibit_blocker, inhibit_body))

    inner = ProgramNode(ProgramKind.COMPOSE, children=(temporal, counterfactual))
    root = ProgramNode(ProgramKind.COMPOSE, children=(inner, inhibit))

    decision = CognitiveLoopR1().deliberate(_request(root, world, task, ledger=ledger))

    expected_paths = {(), (0,), (0, 0), (0, 0, 0), (0, 1), (0, 1, 0), (1,), (1, 0), (1, 1)}
    actual_paths = {step.step_path for step in decision.execution.steps}
    assert actual_paths == expected_paths

    ids = {path: _graph_id(decision, path) for path in expected_paths}
    edges = {(edge.parent_id, edge.child_id) for edge in decision.trace_graph.edges}
    expected_dependency_edges = {
        (ids[(0,)], ids[()]),
        (ids[(1,)], ids[()]),
        (ids[(0, 0)], ids[(0,)]),
        (ids[(0, 1)], ids[(0,)]),
        (ids[(0, 0, 0)], ids[(0, 0)]),
        (ids[(0, 1, 0)], ids[(0, 1)]),
        (ids[(1, 0)], ids[(1,)]),
        (ids[(1, 1)], ids[(1,)]),
    }
    assert expected_dependency_edges.issubset(edges)

    assert decision.trace_graph.nodes[ids[(0, 0, 0)]].payload["world_id"].endswith(":temporal:current:None")
    assert decision.trace_graph.nodes[ids[(0, 1, 0)]].payload["world_id"].endswith(":cf")
    assert decision.trace_graph.nodes[ids[(1, 0)]].payload["truth"] is False
    assert decision.trace_graph.nodes[ids[(1, 1)]].payload["truth"] is True
    assert decision.execution.proof_coverage.complete is True
    assert decision.execution.proof_coverage.coverage == 1.0
