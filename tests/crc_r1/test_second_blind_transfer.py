from benchmarks.crc_second_blind.run import (
    FROZEN_ARCH_SHA,
    BLIND_FAMILIES,
    generate_case_fingerprint,
    run_second_blind,
)

EXPECTED_FREEZE = "97a9c7ed12900969c68ba596e629c70adb398f06"
EXPECTED_FAMILIES = (
    "MEMORY_BRIDGE_NOISE",
    "CAUSAL_CONFOUNDED_INTERVENTION",
    "PLANNING_H2_H5",
    "PROGRAM_NESTED_NOVEL",
    "CREDIT_MULTI_EPISODE",
    "META_CALIBRATION_MIXED",
)


def test_second_blind_is_bound_to_post_fix_freeze():
    assert FROZEN_ARCH_SHA == EXPECTED_FREEZE
    assert BLIND_FAMILIES == EXPECTED_FAMILIES


def test_seed_changes_actual_task_parameters():
    a = generate_case_fingerprint(420001, 0)
    b = generate_case_fingerprint(420002, 0)
    assert a != b


def test_planning_horizons_cover_two_through_five():
    result = run_second_blind(seeds=(420001, 420002, 420003, 420004), repeats=4, budget_units=1.0)
    assert set(result["planning_horizons_seen"]) == {2, 3, 4, 5}


def test_second_blind_protocol_and_metrics_are_mechanical():
    result = run_second_blind(seeds=(420001, 420002), repeats=2, budget_units=1.0)
    p = result["protocol"]
    assert p["kind"] == "post_fix_second_blind_transfer"
    assert p["frozen_arch_sha"] == EXPECTED_FREEZE
    assert p["reuses_first_far_oos_cases"] is False
    assert p["independent_oracle"] is True
    assert p["m32_meta_opened"] is False
    assert p["ftx2_authored"] is False
    assert tuple(p["families"]) == EXPECTED_FAMILIES
    assert result["budget_violations"] == 0
    assert set(result["family_accuracy"]) == set(EXPECTED_FAMILIES)
    assert 0.0 <= result["exact_task_success"] <= 1.0
    assert 0.0 <= result["minimum_family_accuracy"] <= 1.0
    assert result["credit_leakage"] >= 0.0
    assert result["seed_success_std"] >= 0.0
    assert result["verdict"] in {"FAIL", "PARTIAL_TRANSFER", "TRANSFER_SUPPORTED"}


def test_verdict_threshold_is_pre_registered():
    result = run_second_blind(seeds=(420001, 420002), repeats=2, budget_units=1.0)
    exact = result["exact_task_success"]
    minimum = result["minimum_family_accuracy"]
    if exact >= 0.80 and minimum >= 0.50:
        assert result["verdict"] == "TRANSFER_SUPPORTED"
    elif exact >= 0.50:
        assert result["verdict"] == "PARTIAL_TRANSFER"
    else:
        assert result["verdict"] == "FAIL"
