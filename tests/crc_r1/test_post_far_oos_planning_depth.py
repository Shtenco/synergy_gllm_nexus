from nexus_gllm.unified_v3.cognitive.ablation import AblationStage, CognitiveLoopConfig
from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1, CognitiveRequest
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.cognitive.runtime import CognitiveRecursiveCoreR1
from nexus_gllm.unified_v3.cognitive.world_model import EmpiricalWorldModel
from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, TaskOpcode, TaskProgram, WorldFact, WorldHypothesis


def test_flat_priced_future_module_must_not_truncate_required_three_step_search():
    """Post-FAR-OOS DEV regression.

    The frozen FAR-OOS run showed that adaptive meta-control selected depth=2,
    although the future module is charged the same fixed compute cost at depth
    2 and depth 3. The delayed terminal reward is only visible at depth 3.

    This is deliberately a DEV regression derived *after* the preserved
    PARTIAL_TRANSFER verdict; it must never rewrite that verdict.
    """
    model = EmpiricalWorldModel()
    for _ in range(5):
        model.observe("s0", "cash_now", "dead", 0.92)
        model.observe("s0", "invest", "s1", 0.05)
        model.observe("s1", "advance", "s2", 0.10)
        model.observe("s2", "finish", "goal", 2.40)

    relation = "post_far_oos_relation"
    world = WorldHypothesis(
        "post-far-oos-world",
        (
            WorldFact(OperatorSymbol(relation, 2), (Entity("a"), Entity("b")), True),
            WorldFact(OperatorSymbol(relation, 2), (Entity("b"), Entity("c")), True),
        ),
    )
    request = CognitiveRequest(
        episode_id="post-far-oos-planning-depth",
        world=world,
        task=TaskProgram(TaskOpcode.QUERY_RELATION, relation, ("a", "c")),
        program=ProgramNode(ProgramKind.ATOM, f"rule:transitive:{relation}"),
        novelty=0.35,
        uncertainty=0.25,
        planning_state="s0",
        capability_hints=("program_execution", "future_planning"),
    )
    config = CognitiveLoopConfig.for_stage(AblationStage.E_META, budget_units=1.0)
    decision = CognitiveLoopR1(CognitiveRecursiveCoreR1(), model, config=config).deliberate(request)

    assert decision.plan is not None
    assert decision.plan.action == "invest"
    assert decision.plan.depth == 3
    assert decision.compute.spent_units <= decision.compute.budget_units
