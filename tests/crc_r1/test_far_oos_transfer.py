from benchmarks.crc_far_oos.run import FROZEN_ARCH_SHA, FAR_OOS_FAMILIES, run_far_oos


EXPECTED_FREEZE = "6067746d3dbab7a5a0a7388545b73116fd23c25a"
EXPECTED_FAMILIES = (
    "MEMORY_CHAIN_RU",
    "TEMPORAL_SNAPSHOT",
    "CAUSAL_REVERSAL",
    "LONG_HORIZON_PLAN",
    "CREDIT_TRANSFER",
    "UNSEEN_COMPOSITION",
    "CALIBRATED_ABSTENTION",
)


def test_far_oos_is_bound_to_pre_evaluation_architecture_freeze():
    assert FROZEN_ARCH_SHA == EXPECTED_FREEZE
    assert FAR_OOS_FAMILIES == EXPECTED_FAMILIES


def test_far_oos_corpus_is_fresh_and_not_dev_generator_reuse():
    result = run_far_oos(seeds=(91001,), repeats=1, budget_units=1.0)
    p = result["protocol"]
    assert p["kind"] == "frozen_far_oos_transfer"
    assert p["frozen_arch_sha"] == EXPECTED_FREEZE
    assert p["uses_controlled_dev_generator"] is False
    assert p["m32_meta_opened"] is False
    assert p["ftx2_authored"] is False
    assert tuple(p["families"]) == EXPECTED_FAMILIES
    assert all("dev-" not in case_id for case_id in result["case_ids"])


def test_far_oos_reports_transfer_metrics_without_mutating_the_frozen_model():
    result = run_far_oos(seeds=(91001, 91002), repeats=2, budget_units=1.0)
    assert result["protocol"]["seed_count"] == 2
    assert result["total_cases"] > 0
    assert result["budget_violations"] == 0
    assert set(result["family_accuracy"]) == set(EXPECTED_FAMILIES)
    assert 0.0 <= result["exact_task_success"] <= 1.0
    assert 0.0 <= result["proof_complete_rate"] <= 1.0
    assert 0.0 <= result["causal_accuracy"] <= 1.0
    assert 0.0 <= result["planning_accuracy"] <= 1.0
    assert 0.0 <= result["post_feedback_transfer"] <= 1.0
    assert 0.0 <= result["calibrated_abstention"] <= 1.0
    assert result["credit_leakage"] >= 0.0
    assert result["success_per_compute"] >= 0.0
    assert result["seed_success_std"] >= 0.0


def test_far_oos_verdict_is_mechanical_not_hand_written():
    result = run_far_oos(seeds=(91001, 91002), repeats=2, budget_units=1.0)
    assert result["verdict"] in {"FAIL", "PARTIAL_TRANSFER", "TRANSFER_SUPPORTED"}
    if result["exact_task_success"] >= 0.80 and min(result["family_accuracy"].values()) >= 0.50:
        assert result["verdict"] == "TRANSFER_SUPPORTED"
    elif result["exact_task_success"] >= 0.50:
        assert result["verdict"] == "PARTIAL_TRANSFER"
    else:
        assert result["verdict"] == "FAIL"
