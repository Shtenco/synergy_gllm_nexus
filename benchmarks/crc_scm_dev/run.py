from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass

from benchmarks.crc_scm_oracle import LinearSCMOracle, StructuralEquation
from nexus_gllm.unified_v3.cognitive.causal_model import CausalEvidence, CausalEvidenceKind, CausalGraph


REGIMES = (
    "identified_confounded",
    "correlation_only_zero_effect",
    "intervention_only",
    "causal_evidence_conflict",
)


@dataclass(frozen=True)
class SCMCase:
    case_id: str
    equations: tuple[StructuralEquation, ...]
    cause: str
    effect: str
    evidence: tuple[CausalEvidence, ...]
    oracle_identified: bool
    oracle_sign: int
    regime: str


def _chain_scm(rng: random.Random, case_id: str, nodes: int, *, connected: bool) -> tuple[StructuralEquation, ...]:
    names = [f"{case_id}:v{i}" for i in range(nodes)]
    equations = [StructuralEquation(names[0], bias=rng.uniform(-0.25, 0.25))]
    for i in range(1, nodes):
        parents = []
        if connected:
            sign = -1.0 if rng.random() < 0.5 else 1.0
            parents.append((names[i - 1], sign * rng.uniform(0.65, 1.25)))
        elif i > 1:
            # Keep a nontrivial DAG among variables that cannot carry v0 -> vN.
            parent = names[rng.randrange(1, i)]
            sign = -1.0 if rng.random() < 0.5 else 1.0
            parents.append((parent, sign * rng.uniform(0.4, 1.1)))
        if i >= 2 and rng.random() < 0.35:
            parent_index = rng.randrange(0 if connected else 1, i)
            parent = names[parent_index]
            if all(p != parent for p, _ in parents):
                sign = -1.0 if rng.random() < 0.5 else 1.0
                parents.append((parent, sign * rng.uniform(0.2, 0.8)))
        equations.append(StructuralEquation(names[i], tuple(parents), bias=rng.uniform(-0.25, 0.25)))
    return tuple(equations)


def make_case(rng: random.Random, case_id: str, nodes: int, regime: str) -> SCMCase:
    connected = regime != "correlation_only_zero_effect"
    equations = _chain_scm(rng, case_id, nodes, connected=connected)
    scm = LinearSCMOracle(equations)
    cause, effect = equations[0].variable, equations[-1].variable
    structural_sign = scm.effect_sign(cause, effect)
    evidence = []

    if regime == "identified_confounded":
        assert structural_sign != 0
        evidence.extend(
            (
                CausalEvidence(case_id + ":obs", cause, effect, CausalEvidenceKind.OBSERVATIONAL, -0.85 * structural_sign, 0.95),
                CausalEvidence(case_id + ":do", cause, effect, CausalEvidenceKind.INTERVENTIONAL, 0.95 * structural_sign, 1.0),
                CausalEvidence(case_id + ":cf", cause, effect, CausalEvidenceKind.COUNTERFACTUAL, 0.90 * structural_sign, 1.0),
            )
        )
        oracle_identified, oracle_sign = True, structural_sign
    elif regime == "correlation_only_zero_effect":
        assert structural_sign == 0
        spurious = -1 if rng.random() < 0.5 else 1
        evidence.append(CausalEvidence(case_id + ":obs", cause, effect, CausalEvidenceKind.OBSERVATIONAL, 0.90 * spurious, 0.95))
        oracle_identified, oracle_sign = False, 0
    elif regime == "intervention_only":
        assert structural_sign != 0
        evidence.append(CausalEvidence(case_id + ":do", cause, effect, CausalEvidenceKind.INTERVENTIONAL, 0.95 * structural_sign, 1.0))
        oracle_identified, oracle_sign = False, 0
    elif regime == "causal_evidence_conflict":
        assert structural_sign != 0
        evidence.extend(
            (
                CausalEvidence(case_id + ":do", cause, effect, CausalEvidenceKind.INTERVENTIONAL, 0.95 * structural_sign, 1.0),
                CausalEvidence(case_id + ":cf", cause, effect, CausalEvidenceKind.COUNTERFACTUAL, -0.90 * structural_sign, 1.0),
            )
        )
        oracle_identified, oracle_sign = False, 0
    else:
        raise ValueError(regime)

    return SCMCase(case_id, equations, cause, effect, tuple(evidence), oracle_identified, oracle_sign, regime)


def generate(seed: int = 2026100303, cases_per_regime: int = 70) -> tuple[SCMCase, ...]:
    rng = random.Random(seed)
    out = []
    for regime in REGIMES:
        for i in range(cases_per_regime):
            nodes = 4 + rng.randrange(7)
            out.append(make_case(rng, f"scm-dev-{seed}-{regime}-{i}", nodes, regime))
    rng.shuffle(out)
    return tuple(out)


def evaluate(cases: tuple[SCMCase, ...]) -> dict:
    rows = []
    for case in cases:
        graph = CausalGraph()
        for evidence in case.evidence:
            graph.add(evidence)
        pred = graph.edge(case.cause, case.effect)
        correct = pred.identified == case.oracle_identified and pred.effect_sign == case.oracle_sign
        rows.append(
            {
                "case_id": case.case_id,
                "regime": case.regime,
                "nodes": len(case.equations),
                "success": float(correct),
                "false_identification": float(pred.identified and not case.oracle_identified),
                "oracle_sign": case.oracle_sign,
                "predicted_sign": pred.effect_sign,
            }
        )
    by_regime = {
        regime: sum(r["success"] for r in rows if r["regime"] == regime)
        / max(1, sum(1 for r in rows if r["regime"] == regime))
        for regime in REGIMES
    }
    return {
        "protocol": {
            "kind": "post_second_blind_random_scm_dev",
            "oracle": "independent_linear_structural_causal_model",
            "reuses_second_blind_cases": False,
            "m32_meta_opened": False,
            "ftx2_authored": False,
        },
        "case_count": len(rows),
        "accuracy": sum(r["success"] for r in rows) / max(1, len(rows)),
        "false_identification_rate": sum(r["false_identification"] for r in rows) / max(1, len(rows)),
        "by_regime": by_regime,
        "graph_nodes_seen": sorted({r["nodes"] for r in rows}),
    }


def run(seed: int = 2026100303, cases_per_regime: int = 70) -> dict:
    return evaluate(generate(seed, cases_per_regime))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=2026100303)
    parser.add_argument("--cases-per-regime", type=int, default=70)
    parser.add_argument("--out")
    args = parser.parse_args()
    result = run(args.seed, args.cases_per_regime)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
