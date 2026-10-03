from benchmarks.crc_equal_budget.run import run_benchmark
from nexus_gllm.unified_v3.cognitive.ablation import AblationStage, FROZEN_COMPUTE_COSTS


EXPECTED_FAMILIES = (
    "MEMORY_REQUIRED",
    "CAUSAL_TRAP",
    "FUTURE_TRAP",
    "CREDIT_LEARNING",
    "META_RESOURCE",
)


def test_equal_budget_benchmark_executes_all_cumulative_stages_on_same_mixed_corpus():
    result = run_benchmark(seed=1701, repeats=1, budget_units=1.0)

    assert result["protocol"]["kind"] == "controlled_dev_discriminative_cumulative_ablation"
    assert result["protocol"]["budget_units"] == 1.0
    assert result["protocol"]["frozen_cost_schedule"] == FROZEN_COMPUTE_COSTS.__dict__
    assert result["protocol"]["same_case_ids_across_stages"] is True
    assert result["protocol"]["families"] == EXPECTED_FAMILIES
    assert result["protocol"]["final_transfer_evidence"] is False

    stage_names = [stage.value for stage in AblationStage]
    assert list(result["stages"]) == stage_names
    case_ids = None
    for stage_name in stage_names:
        stage = result["stages"][stage_name]
        assert stage["episodes"] > 0
        assert stage["max_compute_spent"] <= 1.0 + 1e-12
        assert stage["budget_violations"] == 0
        assert set(stage["family_accuracy"]) == set(EXPECTED_FAMILIES)
        if case_ids is None:
            case_ids = stage["case_ids"]
        assert stage["case_ids"] == case_ids


def test_discriminative_families_force_behavioral_gains_in_the_intended_stage():
    result = run_benchmark(seed=1702, repeats=2, budget_units=1.0)
    s = result["stages"]

    # Memory is already present in stage A; the benchmark also runs a no-memory
    # counterfactual control to establish that the family is genuinely memory-required.
    assert s["A_MEMORY"]["family_accuracy"]["MEMORY_REQUIRED"] == 1.0
    assert s["A_MEMORY"]["memory_necessity_delta"] > 0.0

    # Correlation alone is a trap; the causal gate must abstain on non-identified causation.
    assert s["A_MEMORY"]["family_accuracy"]["CAUSAL_TRAP"] == 0.0
    assert s["B_CAUSAL"]["family_accuracy"]["CAUSAL_TRAP"] == 1.0

    # Immediate reward is a lure; only future rollout sees the better terminal path.
    assert s["B_CAUSAL"]["family_accuracy"]["FUTURE_TRAP"] == 0.0
    assert s["C_FUTURE"]["family_accuracy"]["FUTURE_TRAP"] == 1.0
    assert s["C_FUTURE"]["long_horizon_planning_accuracy"] == 1.0

    # Feedback must alter the next choice, not merely produce a credit dictionary.
    assert s["C_FUTURE"]["family_accuracy"]["CREDIT_LEARNING"] == 0.0
    assert s["D_CREDIT"]["family_accuracy"]["CREDIT_LEARNING"] == 1.0
    assert s["D_CREDIT"]["post_feedback_adaptation"] == 1.0
    assert s["D_CREDIT"]["credit_leakage"] == 0.0

    # Fixed policy over-computes easy cases and cannot abstain on extreme uncertainty.
    assert s["D_CREDIT"]["family_accuracy"]["META_RESOURCE"] < 1.0
    assert s["E_META"]["family_accuracy"]["META_RESOURCE"] == 1.0
    assert s["E_META"]["calibrated_abstention"] == 1.0

    # Equal family weighting creates the intended cumulative behavioral staircase.
    exact = [s[stage.value]["exact_task_success"] for stage in AblationStage]
    assert exact == sorted(exact)
    assert all(b > a for a, b in zip(exact, exact[1:]))


def test_benchmark_reports_multi_step_proof_compute_efficiency_and_stability_fields():
    result = run_benchmark(seed=1703, repeats=2, budget_units=1.0)
    for stage in result["stages"].values():
        assert 0.0 <= stage["exact_task_success"] <= 1.0
        assert 0.0 <= stage["multi_step_proof_success"] <= 1.0
        assert 0.0 <= stage["causal_trap_accuracy"] <= 1.0
        assert 0.0 <= stage["long_horizon_planning_accuracy"] <= 1.0
        assert 0.0 <= stage["post_feedback_adaptation"] <= 1.0
        assert 0.0 <= stage["calibrated_abstention"] <= 1.0
        assert stage["credit_leakage"] >= 0.0
        assert stage["success_per_compute"] >= 0.0
        assert stage["budget_violations"] == 0

    assert result["deltas"]["B_CAUSAL-A_MEMORY"] > 0.0
    assert result["deltas"]["C_FUTURE-B_CAUSAL"] > 0.0
    assert result["deltas"]["D_CREDIT-C_FUTURE"] > 0.0
    assert result["deltas"]["E_META-D_CREDIT"] > 0.0
    assert result["stability"]["seed_count"] == 1
    assert result["stability"]["per_stage_success_std"]["A_MEMORY"] == 0.0
