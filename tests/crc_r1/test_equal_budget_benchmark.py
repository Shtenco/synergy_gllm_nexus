from benchmarks.crc_equal_budget.run import run_benchmark
from nexus_gllm.unified_v3.cognitive.ablation import AblationStage, FROZEN_COMPUTE_COSTS


def test_equal_budget_benchmark_executes_all_cumulative_stages_on_same_cases():
    result = run_benchmark(seed=1701, repeats=2, budget_units=1.0)

    assert result["protocol"]["kind"] == "controlled_dev_cumulative_ablation"
    assert result["protocol"]["budget_units"] == 1.0
    assert result["protocol"]["frozen_cost_schedule"] == FROZEN_COMPUTE_COSTS.__dict__
    assert result["protocol"]["same_case_ids_across_stages"] is True
    assert result["protocol"]["final_transfer_evidence"] is False

    stage_names = [stage.value for stage in AblationStage]
    assert list(result["stages"]) == stage_names
    case_ids = None
    for stage_name in stage_names:
        stage = result["stages"][stage_name]
        assert stage["episodes"] > 0
        assert stage["max_compute_spent"] <= 1.0 + 1e-12
        assert stage["budget_violations"] == 0
        if case_ids is None:
            case_ids = stage["case_ids"]
        assert stage["case_ids"] == case_ids


def test_benchmark_reports_behavior_not_only_enabled_module_flags():
    result = run_benchmark(seed=1702, repeats=2, budget_units=1.0)
    stages = result["stages"]

    for stage in stages.values():
        assert 0.0 <= stage["answer_accuracy"] <= 1.0
        assert 0.0 <= stage["proof_complete_rate"] <= 1.0
        assert 0.0 <= stage["memory_grounding_rate"] <= 1.0
        assert 0.0 <= stage["causal_identification_rate"] <= 1.0
        assert 0.0 <= stage["planning_action_accuracy"] <= 1.0
        assert 0.0 <= stage["credit_eligible_precision"] <= 1.0
        assert stage["ineligible_positive_credit_mass"] >= 0.0
        assert 0.0 <= stage["adaptive_meta_rate"] <= 1.0

    assert stages["A_MEMORY"]["memory_grounding_rate"] > 0.0
    assert stages["B_CAUSAL"]["causal_identification_rate"] > stages["A_MEMORY"]["causal_identification_rate"]
    assert stages["C_FUTURE"]["planning_action_accuracy"] > stages["B_CAUSAL"]["planning_action_accuracy"]
    assert stages["D_CREDIT"]["credit_eligible_precision"] > stages["C_FUTURE"]["credit_eligible_precision"]
    assert stages["D_CREDIT"]["ineligible_positive_credit_mass"] == 0.0
    assert stages["E_META"]["adaptive_meta_rate"] > stages["D_CREDIT"]["adaptive_meta_rate"]
