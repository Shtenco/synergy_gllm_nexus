from nexus_gllm.unified_v3.cognitive.learned_planner import LearnedFuturePlanner
from nexus_gllm.unified_v3.cognitive.world_model import EmpiricalWorldModel


def _delayed_chain(horizon: int) -> EmpiricalWorldModel:
    model = EmpiricalWorldModel()
    for _ in range(5):
        model.observe("s0", "cash_now", "dead", 0.90)
        for step in range(horizon):
            state = f"s{step}"
            next_state = "goal" if step == horizon - 1 else f"s{step + 1}"
            action = "invest" if step == 0 else f"advance_{step}"
            reward = 2.80 if step == horizon - 1 else 0.04
            model.observe(state, action, next_state, reward)
    return model


def test_anytime_planner_reaches_h5_when_expansion_budget_is_sufficient():
    model = _delayed_chain(5)
    plan = LearnedFuturePlanner(
        model,
        max_depth=8,
        max_expansions=64,
    ).plan("s0")

    assert plan.action == "invest"
    assert plan.depth == 5
    assert plan.expanded_nodes <= 64
    assert plan.max_expansions == 64


def test_planner_reports_budget_exhaustion_instead_of_silently_truncating():
    model = _delayed_chain(5)
    plan = LearnedFuturePlanner(
        model,
        max_depth=8,
        max_expansions=2,
    ).plan("s0")

    assert plan.expanded_nodes == 2
    assert plan.budget_exhausted is True


def test_more_search_compute_never_loses_a_solved_short_horizon_policy():
    model = _delayed_chain(3)
    small = LearnedFuturePlanner(model, max_depth=8, max_expansions=8).plan("s0")
    large = LearnedFuturePlanner(model, max_depth=8, max_expansions=64).plan("s0")

    assert small.action == "invest"
    assert large.action == "invest"
    assert large.value >= small.value
    assert large.expanded_nodes >= small.expanded_nodes
