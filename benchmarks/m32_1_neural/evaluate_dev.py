from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import json
from pathlib import Path

from benchmarks.m32_dev.evaluate import _conflict_attestation
from benchmarks.m32_dev.generator import FAMILIES, generate
from nexus_gllm.unified_v3.cognitive.conversation_shell import ConversationShellR1
from nexus_gllm.unified_v3.cognitive.conversational_reasoner_r2 import (
    ConversationalReasonerR2,
    ConversationalRequest,
)
from nexus_gllm.unified_v3.cognitive.generalized_ingress import GeneralizedIngressR1
from nexus_gllm.unified_v3.cognitive.generalized_ingress_llamacpp import (
    LlamaCppGeneralizedIngressBackend,
    LlamaCppModelRef,
)


class CachingBackend:
    """Cache deterministic neural outcomes by the exact source identities.

    M32-DEV intentionally repeats each of its nine source tuples 20 times. With
    temperature=0 and seed=42, evaluating one neural outcome per unique tuple is
    semantically equivalent while reducing real model calls from 180 to 9.

    Both successful proposals and deterministic backend exceptions are cached.
    Without failure memoization, a malformed deterministic response would cause
    the same model input to be re-run for every duplicate DEV case.
    """

    def __init__(self, backend):
        self.backend = backend
        self.backend_id = getattr(backend, "backend_id", type(backend).__name__)
        self.cache = {}
        self.unique_calls = 0

    @staticmethod
    def _key(request):
        return tuple(
            (source.source_id, source.source_kind.value, source.sha256)
            for source in request.sources
        )

    def propose(self, request):
        key = self._key(request)
        if key not in self.cache:
            self.unique_calls += 1
            try:
                proposal = self.backend.propose(request)
            except Exception as exc:
                self.cache[key] = (False, exc)
                raise
            else:
                self.cache[key] = (True, proposal)
                return proposal

        ok, value = self.cache[key]
        if ok:
            return value
        raise value


def run_with_backend(
    backend,
    *,
    model_sha256: str,
    seed: int = 32001,
    n_per_family: int = 20,
    generation_max_tokens: int = 192,
):
    cases = generate(seed, n_per_family)
    cached = CachingBackend(backend)

    admitted_expected = admitted_ok = 0
    ingress_accepted = 0
    provenance_total = provenance_ok = 0
    solvable = program_ok = e2e_ok = 0
    unsafe_promotions = 0
    unexpected_admissions = 0
    rejection_reasons = Counter()
    family = defaultdict(lambda: {
        "n": 0,
        "task_expected": 0,
        "task_admitted": 0,
        "ingress_accepted": 0,
        "program_admitted": 0,
        "strict": 0,
        "solvable": 0,
        "unexpected_admission": 0,
    })

    for case in cases:
        shell = ConversationShellR1("m32-1-neural:" + case.case_id)
        reasoner = ConversationalReasonerR2(
            shell,
            ingress=GeneralizedIngressR1(cached),
        )
        out = reasoner.answer(
            ConversationalRequest(case.prompt, case.history, case.documents),
            attestations=_conflict_attestation(case),
        )
        row = family[case.family]
        row["n"] += 1

        if case.admission_expected:
            admitted_expected += 1
            row["task_expected"] += 1
            if out.ingress.task is not None:
                admitted_ok += 1
                row["task_admitted"] += 1

        if out.ingress.admission.accepted:
            ingress_accepted += 1
            row["ingress_accepted"] += 1
            provenance_total += 1
            # Ingress acceptance proves semantic/task source spans. If a program
            # exists, program admission independently proves its provenance.
            if out.program_admission is None or out.program_admission.accepted:
                provenance_ok += 1
            if not case.admission_expected:
                unexpected_admissions += 1
                row["unexpected_admission"] += 1
        else:
            rejection_reasons.update(out.ingress.admission.reasons)

        if case.solvable:
            solvable += 1
            row["solvable"] += 1
            if out.program_admission is not None and out.program_admission.accepted:
                program_ok += 1
                row["program_admitted"] += 1
            truth = None if out.decision is None else out.decision.execution.execution.truth
            if truth is case.expected_truth:
                e2e_ok += 1
                row["strict"] += 1

        # Assertions may participate only in transient execution context.
        unsafe_promotions += len(shell.world.facts)

    by_family = {}
    for name in FAMILIES:
        row = family[name]
        n = max(1, row["n"])
        tden = max(1, row["task_expected"])
        sden = max(1, row["solvable"])
        by_family[name] = {
            "n": row["n"],
            "ingress_acceptance": row["ingress_accepted"] / n,
            "task_admission": row["task_admitted"] / tden if row["task_expected"] else None,
            "program_admission_solvable": row["program_admitted"] / sden if row["solvable"] else None,
            "e2e_strict_solvable": row["strict"] / sden if row["solvable"] else None,
            "unexpected_admission": row["unexpected_admission"] / n,
        }

    return {
        "schema": "nexus.m32_1.neural_dev.v1",
        "benchmark": "M32-DEV-NEURAL",
        "seed": seed,
        "cases": len(cases),
        "clean_oos": False,
        "neural_quality_claim": True,
        "ftx1_used_as_clean_oos": False,
        "model_sha256": model_sha256,
        "backend_id": cached.backend_id,
        "generation": {
            "temperature": 0.0,
            "seed": 42,
            "max_tokens": int(generation_max_tokens),
        },
        "unique_neural_calls": cached.unique_calls,
        "ingress_acceptance": ingress_accepted / max(1, len(cases)),
        "task_admission": admitted_ok / max(1, admitted_expected),
        "provenance_validity": provenance_ok / max(1, provenance_total),
        "program_admission_solvable": program_ok / max(1, solvable),
        "e2e_strict_solvable": e2e_ok / max(1, solvable),
        "unsafe_authority_promotions": unsafe_promotions,
        "unexpected_admissions": unexpected_admissions,
        "rejection_reasons": dict(sorted(rejection_reasons.items())),
        "by_family": by_family,
    }


def run(
    *,
    model_path: str,
    endpoint: str,
    expected_sha256: str,
    seed: int = 32001,
    n_per_family: int = 20,
    max_tokens: int = 192,
):
    backend = LlamaCppGeneralizedIngressBackend(
        LlamaCppModelRef(
            model_path=model_path,
            expected_sha256=expected_sha256,
            endpoint=endpoint,
            timeout_s=60.0,
            seed=42,
            max_tokens=int(max_tokens),
        )
    )
    return run_with_backend(
        backend,
        model_sha256=backend.verified_model_sha256,
        seed=seed,
        n_per_family=n_per_family,
        generation_max_tokens=max_tokens,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--sha256", required=True)
    ap.add_argument("--endpoint", default="http://127.0.0.1:8080")
    ap.add_argument("--seed", type=int, default=32001)
    ap.add_argument("--n-per-family", type=int, default=20)
    ap.add_argument("--max-tokens", type=int, default=192)
    ap.add_argument("--output")
    args = ap.parse_args()
    report = run(
        model_path=args.model,
        endpoint=args.endpoint,
        expected_sha256=args.sha256,
        seed=args.seed,
        n_per_family=args.n_per_family,
        max_tokens=args.max_tokens,
    )
    text = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
