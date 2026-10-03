from nexus_gllm.unified_v3.cognitive.ablation import AblationStage, CognitiveLoopConfig
from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1, CognitiveRequest
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.cognitive.reward import RewardVector
from nexus_gllm.unified_v3.cognitive.runtime import CognitiveRecursiveCoreR1
from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, TaskOpcode, TaskProgram, WorldFact, WorldHypothesis
from nexus_gllm.unified_v3.temporal import TemporalLedger


def _atom(symbol: str, *, operator: str | None = None, src: str | None = None, dst: str | None = None, tag: str | None = None) -> ProgramNode:
    params = []
    if operator is not None:
        params.extend((("query_operator", operator), ("query_src", src), ("query_dst", dst)))
    if tag is not None:
        params.append(("tag", tag))
    return ProgramNode(ProgramKind.ATOM, symbol, params=tuple(params))


def _world() -> WorldHypothesis:
    relation = OperatorSymbol("r", 2)
    return WorldHypothesis(
        "credit-world",
        (
            WorldFact(relation, (Entity("a"), Entity("b")), True),
            WorldFact(relation, (Entity("b"), Entity("c")), True),
        ),
    )


def _request(program: ProgramNode, *, world: WorldHypothesis | None = None, task: TaskProgram | None = None, memory_tags=(), ledger=None) -> CognitiveRequest:
    return CognitiveRequest(
        episode_id="credit-causality",
        world=world or _world(),
        task=task or TaskProgram(TaskOpcode.QUERY_RELATION, "r", ("a", "c")),
        program=program,
        memory_tags=tuple(memory_tags),
        temporal_ledger=ledger,
        novelty=0.2,
        uncertainty=0.2,
        predicted_outcome_reward=0.0,
    )


def _graph_id(decision, path: tuple[int, ...]) -> str:
    step = next(step for step in decision.execution.steps if step.step_path == path)
    return "program:" + decision.execution.step_identity(step)


def _stage_d(core=None) -> CognitiveLoopR1:
    return CognitiveLoopR1(core=core, config=CognitiveLoopConfig.for_stage(AblationStage.D_CREDIT, budget_units=1.0))


def test_verified_nested_proof_gets_monotone_credit_without_fixed_meta_interception():
    left = _atom("rule:transitive:r", tag="left")
    right = _atom("rule:transitive:r", tag="right")
    root = ProgramNode(ProgramKind.COMPOSE, children=(left, right))
    loop = _stage_d()
    decision = loop.deliberate(_request(root))
    outcome = loop.observe(decision, RewardVector(task=1.0))

    root_id = _graph_id(decision, ())
    left_id = _graph_id(decision, (0,))
    right_id = _graph_id(decision, (1,))

    assert outcome.credit[root_id] > outcome.credit[left_id] > 0.0
    assert outcome.credit[root_id] > outcome.credit[right_id] > 0.0
    assert outcome.credit.get("meta", 0.0) == 0.0


def test_unverified_dependency_and_unverified_root_receive_no_positive_credit():
    proved = _atom("rule:transitive:r", operator="r", src="a", dst="c", tag="proved")
    unresolved = _atom("rule:transitive:r", operator="r", src="a", dst="z", tag="unresolved")
    root = ProgramNode(ProgramKind.COMPOSE, children=(proved, unresolved))
    loop = _stage_d()
    decision = loop.deliberate(_request(root))
    outcome = loop.observe(decision, RewardVector(task=1.0))

    root_id = _graph_id(decision, ())
    unresolved_id = _graph_id(decision, (1,))
    assert decision.trace_graph.nodes[root_id].payload["verified"] is False
    assert decision.trace_graph.nodes[unresolved_id].payload["verified"] is False
    assert outcome.credit.get(root_id, 0.0) <= 0.0
    assert outcome.credit.get(unresolved_id, 0.0) <= 0.0


def test_retrieved_but_ungrounded_memory_does_not_intercept_proof_credit():
    core = CognitiveRecursiveCoreR1()
    core.memory.add_raw({"irrelevant": True}, confidence=1.0, tags=("noise",))
    root = _atom("rule:transitive:r")
    loop = _stage_d(core)
    decision = loop.deliberate(_request(root, memory_tags=("noise",)))
    outcome = loop.observe(decision, RewardVector(task=1.0))

    memory_nodes = [node_id for node_id, node in decision.trace_graph.nodes.items() if node.kind == "memory"]
    assert memory_nodes
    assert all(decision.trace_graph.nodes[node_id].payload["grounded"] is False for node_id in memory_nodes)
    assert all(outcome.credit.get(node_id, 0.0) == 0.0 for node_id in memory_nodes)
    assert outcome.credit.get("meta", 0.0) == 0.0


def test_skipped_inhibit_body_has_no_credit_entry():
    block = OperatorSymbol("block", 2)
    relation = OperatorSymbol("r", 2)
    world = WorldHypothesis(
        "credit-inhibit-world",
        (
            WorldFact(block, (Entity("x"), Entity("y")), True),
            WorldFact(relation, (Entity("a"), Entity("b")), True),
            WorldFact(relation, (Entity("b"), Entity("c")), True),
        ),
    )
    blocker = _atom("rule:transitive:block", operator="block", src="x", dst="y")
    body = _atom("rule:transitive:r")
    root = ProgramNode(ProgramKind.INHIBIT, children=(blocker, body))
    loop = _stage_d()
    decision = loop.deliberate(_request(root, world=world))
    outcome = loop.observe(decision, RewardVector(task=1.0))

    body_prefix = "program:" + body.program_id
    assert all(not node_id.startswith(body_prefix) for node_id in decision.trace_graph.nodes)
    assert all(not node_id.startswith(body_prefix) for node_id in outcome.credit)


def test_counterfactual_occurrence_credit_stays_distinct_from_actual_occurrence():
    world = WorldHypothesis(
        "credit-cf-world",
        (WorldFact(OperatorSymbol("r", 2), (Entity("a"), Entity("b")), True),),
    )
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "r", ("a", "b"))
    shared = _atom("rule:transitive:r")
    cf = ProgramNode(
        ProgramKind.COUNTERFACTUAL,
        children=(shared,),
        params=(("kind", "ADD_FACT"), ("operator", "q"), ("src", "x"), ("dst", "y")),
    )
    root = ProgramNode(ProgramKind.COMPOSE, children=(shared, cf))
    loop = _stage_d()
    decision = loop.deliberate(_request(root, world=world, task=task))
    outcome = loop.observe(decision, RewardVector(task=1.0))

    actual_id = _graph_id(decision, (0,))
    cf_id = _graph_id(decision, (1, 0))
    assert actual_id != cf_id
    assert outcome.credit[actual_id] > 0.0
    assert outcome.credit[cf_id] > 0.0
    assert decision.trace_graph.nodes[actual_id].payload["world_id"] == "credit-cf-world"
    assert decision.trace_graph.nodes[cf_id].payload["world_id"].endswith(":cf")


def test_temporal_credit_is_bound_to_snapshot_occurrence():
    ledger = (
        TemporalLedger()
        .assert_fact("state", "node", "old", 1)
        .assert_fact("state", "node", "new", 10, supersede=True)
    )
    world = WorldHypothesis("credit-temporal-world", ())
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "state", ("node", "old"))
    child = _atom("rule:transitive:state", operator="state", src="node", dst="old")
    root = ProgramNode(ProgramKind.TEMPORAL, children=(child,), params=(("time", "5"),))
    loop = _stage_d()
    decision = loop.deliberate(_request(root, world=world, task=task, ledger=ledger))
    outcome = loop.observe(decision, RewardVector(task=1.0))

    root_id = _graph_id(decision, ())
    child_id = _graph_id(decision, (0,))
    expected_world = "credit-temporal-world:temporal:at:5"
    assert outcome.credit[root_id] > outcome.credit[child_id] > 0.0
    assert decision.trace_graph.nodes[root_id].payload["world_id"] == expected_world
    assert decision.trace_graph.nodes[child_id].payload["world_id"] == expected_world
