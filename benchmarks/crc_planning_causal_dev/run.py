from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass

from nexus_gllm.unified_v3.cognitive.causal_model import (
    CausalEvidence,
    CausalEvidenceKind,
    CausalGraph,
)
from nexus_gllm.unified_v3.cognitive.learned_planner import LearnedFuturePlanner
from nexus_gllm.unified_v3.cognitive.world_model import EmpiricalWorldModel


PLANNING_HORIZONS = tuple(range(2, 9))
PLANNING_EXPANSION_BUDGETS = (4, 8, 16, 32, 64)


@dataclass(frozen=True)
class PlanningCase:
    case_id: str
    model: EmpiricalWorldModel
    start: str
    oracle_action: str
    horizon: int
    branching: int
    exact_delayed_value: float
    immediate_value: float


@dataclass(frozen=True)
class CausalCase:
    case_id: str
    evidence: tuple[CausalEvidence, ...]
    cause: str
    effect: str
    oracle_identified: bool
    oracle_sign: int
    graph_nodes: int
    regime: str


def _discounted(rewards: tuple[float, ...], gamma: float = 0.95) -> float:
    return sum((gamma ** i) * reward for i, reward in enumerate(rewards))


def make_planning_case(rng: random.Random, case_id: str, horizon: int, branching: int) -> PlanningCase:
    model = EmpiricalWorldModel()
    start = f"{case_id}:s0"
    invest = f"a_invest:{case_id}"
    cash = f"z_cash:{case_id}"
    dead = f"{case_id}:dead"
    immediate = rng.uniform(0.62, 0.98)
    intermediate = tuple(rng.uniform(-0.02, 0.09) for _ in range(max(0, horizon - 1)))
    terminal = rng.uniform(1.75, 3.10)
    rewards = intermediate + (terminal,)
    delayed = _discounted(rewards)
    oracle = invest if delayed > immediate else cash

    states = [start] + [f"{case_id}:s{i}" for i in range(1, horizon)] + [f"{case_id}:goal"]
    actions = [invest] + [f"b_step_{i}:{case_id}" for i in range(1, horizon)]
    for _ in range(5):
        model.observe(start, cash, dead, immediate)
        for step, action in enumerate(actions):
            model.observe(states[step], action, states[step + 1], rewards[step])
        # Root distractors create branching without sharing the delayed chain.
        for j in range(max(0, branching - 2)):
            distractor = f"m_distractor_{j}:{case_id}"
            model.observe(start, distractor, f"{case_id}:trap:{j}", rng.uniform(-0.20, 0.55))

    return PlanningCase(case_id, model, start, oracle, horizon, branching, delayed, immediate)


def generate_planning(seed: int = 2026100301, repeats_per_horizon: int = 24) -> tuple[PlanningCase, ...]:
    rng = random.Random(seed)
    out = []
    for horizon in PLANNING_HORIZONS:
        for repeat in range(repeats_per_horizon):
            branching = 2 + rng.randrange(4)
            out.append(make_planning_case(rng, f"plan-dev-{seed}-{horizon}-{repeat}", horizon, branching))
    return tuple(out)


def evaluate_planning(cases: tuple[PlanningCase, ...], expansion_budgets=PLANNING_EXPANSION_BUDGETS) -> dict:
    by_budget = {}
    for cap in expansion_budgets:
        rows = []
        for case in cases:
            plan = LearnedFuturePlanner(
                case.model,
                max_depth=12,
                fanout=max(5, case.branching),
                beam_width=16,
                max_expansions=int(cap),
            ).plan(case.start)
            rows.append(
                {
                    "case_id": case.case_id,
                    "horizon": case.horizon,
                    "branching": case.branching,
                    "success": float(plan.action == case.oracle_action),
                    "expanded_nodes": plan.expanded_nodes,
                    "budget_exhausted": plan.budget_exhausted,
                    "plan_depth": plan.depth,
                }
            )
        accuracy = sum(r["success"] for r in rows) / max(1, len(rows))
        by_horizon = {
            str(h): sum(r["success"] for r in rows if r["horizon"] == h)
            / max(1, sum(1 for r in rows if r["horizon"] == h))
            for h in PLANNING_HORIZONS
        }
        by_budget[str(cap)] = {
            "accuracy": accuracy,
            "by_horizon": by_horizon,
            "mean_expansions": sum(r["expanded_nodes"] for r in rows) / max(1, len(rows)),
            "budget_exhaustion_rate": sum(float(r["budget_exhausted"]) for r in rows) / max(1, len(rows)),
        }
    acc = [by_budget[str(cap)]["accuracy"] for cap in expansion_budgets]
    monotone = all(b + 1e-12 >= a for a, b in zip(acc, acc[1:]))
    return {
        "case_count": len(cases),
        "horizons": list(PLANNING_HORIZONS),
        "expansion_budgets": list(expansion_budgets),
        "by_budget": by_budget,
        "accuracy_monotone_non_decreasing": monotone,
    }


def _signed(rng: random.Random, lo: float, hi: float, sign: int) -> float:
    return float(sign) * rng.uniform(lo, hi)


def make_causal_case(rng: random.Random, case_id: str, graph_nodes: int, regime: str) -> CausalCase:
    cause = f"{case_id}:x"
    effect = f"{case_id}:y"
    sign = -1 if rng.random() < 0.5 else 1
    evidence = []

    if regime == "identified_confounded":
        # The observational channel is deliberately reversed by confounding;
        # intervention and counterfactual agree on the structural effect.
        evidence.extend(
            (
                CausalEvidence(case_id + ":obs", cause, effect, CausalEvidenceKind.OBSERVATIONAL, _signed(rng, 0.55, 0.95, -sign), rng.uniform(0.75, 1.0)),
                CausalEvidence(case_id + ":do", cause, effect, CausalEvidenceKind.INTERVENTIONAL, _signed(rng, 0.82, 1.0, sign), rng.uniform(0.90, 1.0)),
                CausalEvidence(case_id + ":cf", cause, effect, CausalEvidenceKind.COUNTERFACTUAL, _signed(rng, 0.72, 0.98, sign), rng.uniform(0.88, 1.0)),
            )
        )
        identified, oracle_sign = True, sign
    elif regime == "correlation_only":
        evidence.append(CausalEvidence(case_id + ":obs", cause, effect, CausalEvidenceKind.OBSERVATIONAL, _signed(rng, 0.65, 1.0, sign), rng.uniform(0.8, 1.0)))
        identified, oracle_sign = False, 0
    elif regime == "causal_disagreement":
        evidence.extend(
            (
                CausalEvidence(case_id + ":do", cause, effect, CausalEvidenceKind.INTERVENTIONAL, _signed(rng, 0.82, 1.0, sign), rng.uniform(0.9, 1.0)),
                CausalEvidence(case_id + ":cf", cause, effect, CausalEvidenceKind.COUNTERFACTUAL, _signed(rng, 0.82, 1.0, -sign), rng.uniform(0.9, 1.0)),
            )
        )
        identified, oracle_sign = False, 0
    elif regime == "intervention_only":
        evidence.append(CausalEvidence(case_id + ":do", cause, effect, CausalEvidenceKind.INTERVENTIONAL, _signed(rng, 0.82, 1.0, sign), rng.uniform(0.9, 1.0)))
        identified, oracle_sign = False, 0
    else:
        raise ValueError(regime)

    # Irrelevant signed edges enlarge the evidence graph without changing the
    # direct x->y oracle. They exercise graph bookkeeping and cycle traversal.
    for i in range(max(0, graph_nodes - 2)):
        a = f"{case_id}:n{i}"
        b = f"{case_id}:n{i+1}"
        s = -1 if rng.random() < 0.5 else 1
        evidence.extend(
            (
                CausalEvidence(f"{case_id}:irr-do:{i}", a, b, CausalEvidenceKind.INTERVENTIONAL, _signed(rng, 0.80, 1.0, s), 1.0),
                CausalEvidence(f"{case_id}:irr-cf:{i}", a, b, CausalEvidenceKind.COUNTERFACTUAL, _signed(rng, 0.75, 1.0, s), 1.0),
            )
        )

    return CausalCase(case_id, tuple(evidence), cause, effect, identified, oracle_sign, graph_nodes, regime)


def generate_causal(seed: int = 2026100302, cases_per_regime: int = 60) -> tuple[CausalCase, ...]:
    rng = random.Random(seed)
    regimes = ("identified_confounded", "correlation_only", "causal_disagreement", "intervention_only")
    out = []
    for regime in regimes:
        for i in range(cases_per_regime):
            nodes = 4 + rng.randrange(7)
            out.append(make_causal_case(rng, f"causal-dev-{seed}-{regime}-{i}", nodes, regime))
    rng.shuffle(out)
    return tuple(out)


def evaluate_causal(cases: tuple[CausalCase, ...]) -> dict:
    rows = []
    for case in cases:
        graph = CausalGraph()
        for evidence in case.evidence:
            graph.add(evidence)
        edge = graph.edge(case.cause, case.effect)
        correct = edge.identified == case.oracle_identified and edge.effect_sign == case.oracle_sign
        false_identification = edge.identified and not case.oracle_identified
        rows.append(
            {
                "case_id": case.case_id,
                "regime": case.regime,
                "graph_nodes": case.graph_nodes,
                "correct": float(correct),
                "false_identification": float(false_identification),
            }
        )
    by_regime = {
        regime: sum(r["correct"] for r in rows if r["regime"] == regime)
        / max(1, sum(1 for r in rows if r["regime"] == regime))
        for regime in sorted({c.regime for c in cases})
    }
    return {
        "case_count": len(cases),
        "accuracy": sum(r["correct"] for r in rows) / max(1, len(rows)),
        "false_identification_rate": sum(r["false_identification"] for r in rows) / max(1, len(rows)),
        "by_regime": by_regime,
        "graph_nodes_seen": sorted({c.graph_nodes for c in cases}),
    }


def run_dev(seed: int = 20261003) -> dict:
    planning = evaluate_planning(generate_planning(seed * 100 + 1))
    causal = evaluate_causal(generate_causal(seed * 100 + 2))
    return {
        "protocol": {
            "kind": "post_second_blind_planning_causal_dev",
            "reuses_second_blind_cases": False,
            "planning_oracle": "exact_sampled_discounted_rewards",
            "causal_oracle": "independent_regime_structural_rule",
            "m32_meta_opened": False,
            "ftx2_authored": False,
        },
        "planning": planning,
        "causal": causal,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261003)
    parser.add_argument("--out")
    args = parser.parse_args()
    result = run_dev(args.seed)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
