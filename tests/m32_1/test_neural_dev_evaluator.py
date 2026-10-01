from __future__ import annotations

from nexus_gllm.unified_v3.cognitive.generalized_ingress import GeneralizedIngressProposal
from benchmarks.m32_1_neural.evaluate_dev import run_with_backend


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


def test_neural_dev_evaluator_caches_identical_inputs_and_never_exposes_gold():
    backend = CountingBackend()
    report = run_with_backend(
        backend,
        model_sha256="a" * 64,
        seed=32001,
        n_per_family=2,
    )
    assert report["schema"] == "nexus.m32_1.neural_dev.v1"
    assert report["benchmark"] == "M32-DEV-NEURAL"
    assert report["cases"] == 18
    assert report["unique_neural_calls"] == 9
    assert len(backend.calls) == 9
    assert report["model_sha256"] == "a" * 64
    assert report["neural_quality_claim"] is True
    assert report["clean_oos"] is False
    assert report["ftx1_used_as_clean_oos"] is False
    assert "task_admission" in report
    assert "provenance_validity" in report
    assert "program_admission_solvable" in report
    assert "e2e_strict_solvable" in report
    assert "unsafe_authority_promotions" in report
    assert set(report["by_family"]) == {
        "ru", "en", "mixed", "history", "documents", "composition",
        "counterfactual", "conflict", "adversarial",
    }
