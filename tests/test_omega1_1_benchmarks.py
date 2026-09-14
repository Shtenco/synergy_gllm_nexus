from nexus_gllm.compiler_proposal import NeuralParseProposal
from benchmarks.run_compiler_benchmark import score_compiler_predictions
from benchmarks.run_temporal_benchmark import run_temporal_smoke
from benchmarks.run_consolidation_benchmark import run_consolidation_smoke


def test_compiler_metrics_count_strict_structure_and_invalid_acceptance():
    gold = [{
        "id": "x",
        "input_text": "Антон старше Бориса",
        "compiler_target": {
            "relation": "older_than",
            "subject_text": "Антон",
            "object_text": "Бориса",
            "subject_span": [0, 5],
            "object_span": [13, 19],
        },
    }]
    predictions = [NeuralParseProposal(
        relation="older_than",
        subject_text="Антон",
        object_text="Бориса",
        subject_span=(0, 5),
        object_span=(13, 19),
        confidence=0.99,
        kind="statement",
    )]
    metrics = score_compiler_predictions(gold, predictions)
    assert metrics["relation_accuracy"] == 1.0
    assert metrics["strict_structural_exact_match"] == 1.0
    assert metrics["invalid_accepted_proposal_rate"] == 0.0


def test_temporal_smoke_covers_closure_cycles_and_retraction():
    result = run_temporal_smoke()
    assert result["passed"] == result["total"]
    assert result["total"] >= 5


def test_consolidation_smoke_preserves_history_and_resolves_conflicts():
    result = run_consolidation_smoke()
    assert result["passed"] == result["total"]
    assert result["total"] >= 4
