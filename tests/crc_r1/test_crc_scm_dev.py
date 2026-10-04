from benchmarks.crc_scm_dev.run import REGIMES, run


def test_random_scm_dev_is_fresh_structural_and_sealed():
    result = run(seed=2026100303, cases_per_regime=12)
    protocol = result["protocol"]
    assert protocol["kind"] == "post_second_blind_random_scm_dev"
    assert protocol["oracle"] == "independent_linear_structural_causal_model"
    assert protocol["reuses_second_blind_cases"] is False
    assert protocol["m32_meta_opened"] is False
    assert protocol["ftx2_authored"] is False


def test_random_scm_dev_covers_graph_sizes_and_signed_effects_without_false_identification():
    result = run(seed=2026100303, cases_per_regime=70)
    assert result["case_count"] == 70 * len(REGIMES)
    assert result["graph_nodes_seen"] == list(range(4, 11))
    assert result["accuracy"] >= 0.95
    assert result["false_identification_rate"] == 0.0
    assert min(result["by_regime"].values()) >= 0.90
