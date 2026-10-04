from nexus_gllm.unified_v3.cognitive.ablation import AblationStage, CognitiveLoopConfig
from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1, CognitiveRequest
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.cognitive.runtime import CognitiveRecursiveCoreR1
from nexus_gllm.unified_v3.cognitive.world_model import EmpiricalWorldModel
from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, TaskOpcode, TaskProgram, WorldFact, WorldHypothesis


def test_future_planning_capability_uses_separate_horizon_and_expansion_budget_through_cognitive_loop():
    horizon = 8
    model = EmpiricalWorldModel()
    for _ in range(5):
        model.observe("s0", "cash_now", "dead", 0.85)
        for step in range(horizon):
            state = f"s{step}"
            next_state = "goal" if step == horizon - 1 else f"s{step + 1}"
            action = "invest" if step == 0 else f"advance_{step}"
            reward = 3.0 if step == horizon - 1 else 0.04
            model.observe(state, action, next_state, reward)

    relation = "post_second_blind_h8"
    world = WorldHypothesis(
        "post-second-blind-h8-world",
        (
            WorldFact(OperatorSymbol(relation, 2), (Entity("a"), Entity("b")), True),
            WorldFact(OperatorSymbol(relation, 2), (Entity("b"), Entity("c")), True),
        ),
    )
    request = CognitiveRequest(
        episode_id="post-second-blind-h8",
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

    assert decision.meta.branch_depth == decision.state.budget.max_planning_depth
    assert decision.meta.branch_depth >= horizon
    assert decision.plan is not None
    assert decision.plan.action == "invest"
    assert decision.plan.depth == horizon
    assert decision.plan.max_expansions == decision.state.budget.max_planning_expansions
    assert decision.plan.expanded_nodes <= decision.plan.max_expansions
    assert decision.compute.spent_units <= decision.compute.budget_units
