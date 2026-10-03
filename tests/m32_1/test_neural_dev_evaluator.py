from __future__ import annotations

from nexus_gllm.unified_v3.cognitive.generalized_ingress import GeneralizedIngressProposal
from benchmarks.m32_1_neural.evaluate_dev import DEV_GENERATION_MAX_TOKENS, run_with_backend


class CountingBackend:
    backend_id = "counting-neural-stub"

    def __init__(self):
        self.calls = []

    def propose(self, request):
        # Neural backend contract receives sources only, never DevCase gold fields.
        assert hasattr(request, "sources")
        assert not hasattr(request, "facts")
        assert not hasattr(request, "task")
        assert not hasattr(request, "program")
        self.calls.append(tuple((s.source_id, s.sha256) for s in request.sources))
        return GeneralizedIngressProposal(self.backend_id)


class DeterministicFailingBackend:
    backend_id = "deterministic-failing-neural-stub"

    def __init__(self):
        self.calls = []

    def propose(self, request):
        self.calls.append(tuple((s.source_id, s.sha256) for s in request.sources))
        raise ValueError("deterministic_bad_proposal")


def test_dev_v3_generation_budget_is_pinned():
    assert DEV_GENERATION_MAX_TOKENS == 320


def test_neural_dev_evaluator_caches_identical_inputs_and_never_exposes_gold():
    backend = CountingBackend()
    report = run_with_backend(
        backend,
        model_sha256="a" * 64,
        seed=32001,
        n_per_family=2,
        generation_max_tokens=DEV_GENERATION_MAX_TOKENS,
    )
    assert report["schema"] == "nexus.m32_1.neural_dev.v2"
    assert report["benchmark"] == "M32-DEV-NEURAL"
    assert report["cases"] == 18
    assert report["unique_neural_calls"] == 9
    assert len(backend.calls) == 9
    assert report["model_sha256"] == "a" * 64
    assert report["generation"] == {"temperature": 0.0, "seed": 42, "max_tokens": 320}
    assert report["neural_quality_claim"] is True
    assert report["clean_oos"] is False
    assert report["ftx1_used_as_clean_oos"] is False
    for key in (
        "task_admission", "provenance_validity", "program_admission_solvable",
        "e2e_strict_solvable", "unsafe_authority_promotions",
        "semantic_exact_expected", "task_exact_expected",
        "program_shape_exact_solvable", "negative_rejection_rate",
    ):
        assert key in report
    assert report["semantic_exact_expected"] == 0.0
    assert report["task_exact_expected"] == 0.0
    assert report["program_shape_exact_solvable"] == 0.0
    assert report["negative_rejection_rate"] == 0.0
    assert set(report["by_family"]) == {
        "ru", "en", "mixed", "history", "documents", "composition",
        "counterfactual", "conflict", "adversarial",
    }
    assert all("semantic_exact" in row for row in report["by_family"].values())
    assert all("task_exact" in row for row in report["by_family"].values())


def test_deterministic_backend_failures_are_memoized_by_exact_input():
    backend = DeterministicFailingBackend()
    report = run_with_backend(
        backend,
        model_sha256="b" * 64,
        seed=32001,
        n_per_family=2,
        generation_max_tokens=DEV_GENERATION_MAX_TOKENS,
    )
    assert report["cases"] == 18
    assert report["unique_neural_calls"] == 9
    assert len(backend.calls) == 9
    assert report["ingress_acceptance"] == 0.0
    assert report["task_admission"] == 0.0
    assert report["semantic_exact_expected"] == 0.0
    assert report["task_exact_expected"] == 0.0
    assert report["program_shape_exact_solvable"] == 0.0
    assert report["negative_rejection_rate"] == 1.0
    assert report["generation"]["max_tokens"] == 320
