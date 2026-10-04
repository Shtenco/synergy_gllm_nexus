from benchmarks.crc_planning_causal_dev.run import (
    PLANNING_EXPANSION_BUDGETS,
    PLANNING_HORIZONS,
    run_dev,
)


def test_planning_causal_dev_protocol_is_fresh_and_sealed():
    result = run_dev(seed=20261003)
    protocol = result["protocol"]
    assert protocol["kind"] == "post_second_blind_planning_causal_dev"
    assert protocol["reuses_second_blind_cases"] is False
    assert protocol["planning_oracle"] == "exact_sampled_discounted_rewards"
    assert protocol["causal_oracle"] == "independent_regime_structural_rule"
    assert protocol["m32_meta_opened"] is False
    assert protocol["ftx2_authored"] is False


def test_planning_dev_covers_h2_h8_and_scales_non_decreasing_with_expansions():
    planning = run_dev(seed=20261003)["planning"]
    assert tuple(planning["horizons"]) == PLANNING_HORIZONS
    assert tuple(planning["expansion_budgets"]) == PLANNING_EXPANSION_BUDGETS
    assert planning["accuracy_monotone_non_decreasing"] is True
    assert planning["by_budget"]["64"]["accuracy"] >= 0.95
    assert min(planning["by_budget"]["64"]["by_horizon"].values()) >= 0.90


def test_causal_dev_covers_random_graph_sizes_and_avoids_false_identification():
    causal = run_dev(seed=20261003)["causal"]
    assert causal["graph_nodes_seen"] == list(range(4, 11))
    assert causal["accuracy"] >= 0.95
    assert causal["false_identification_rate"] == 0.0
    assert set(causal["by_regime"]) == {
        "causal_disagreement",
        "correlation_only",
        "identified_confounded",
        "intervention_only",
    }
