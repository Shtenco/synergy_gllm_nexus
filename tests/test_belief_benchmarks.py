from benchmarks.run_belief_benchmark import belief_metrics
from benchmarks.run_continual_benchmark import continual_metrics
from benchmarks.run_forgetting_benchmark import forgetting_metrics


def test_belief_metrics_are_hand_computable():
    rows = [
        {"expected": 1.0, "posterior": 0.9, "status_ok": True, "contradiction_expected": True, "contradiction_found": True},
        {"expected": 0.0, "posterior": 0.2, "status_ok": True, "contradiction_expected": False, "contradiction_found": False},
    ]
    result = belief_metrics(rows)
    assert result["status_accuracy"] == 1.0
    assert abs(result["brier_score"] - 0.025) < 1e-12
    assert result["contradiction_precision"] == 1.0
    assert result["contradiction_recall"] == 1.0


def test_continual_metrics_report_gain_and_retention():
    result = continual_metrics(baseline_new=0.60, candidate_new=0.72, baseline_legacy=0.90, candidate_legacy=0.88)
    assert abs(result["new_task_gain"] - 0.12) < 1e-12
    assert abs(result["legacy_retention"] - (0.88 / 0.90)) < 1e-12


def test_forgetting_metrics_report_positive_drop():
    result = forgetting_metrics(before=0.95, after=0.90, protected_before=1.0, protected_after=1.0)
    assert abs(result["forgetting_delta"] - 0.05) < 1e-12
    assert result["protected_exact_retention"] == 1.0
