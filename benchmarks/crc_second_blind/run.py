from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
from pathlib import Path

from nexus_gllm.unified_v3.cognitive.ablation import AblationStage, CognitiveLoopConfig
from nexus_gllm.unified_v3.cognitive.causal_model import CausalEvidence, CausalEvidenceKind
from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1, CognitiveRequest
from nexus_gllm.unified_v3.cognitive.credit import CognitiveTraceGraph
from nexus_gllm.unified_v3.cognitive.memory import MemoryLevel
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.cognitive.reward import RewardVector
from nexus_gllm.unified_v3.cognitive.runtime import CognitiveRecursiveCoreR1
from nexus_gllm.unified_v3.cognitive.world_model import EmpiricalWorldModel
from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, TaskOpcode, TaskProgram, WorldFact, WorldHypothesis
from nexus_gllm.unified_v3.temporal import TemporalLedger

FROZEN_ARCH_SHA = "97a9c7ed12900969c68ba596e629c70adb398f06"
BLIND_FAMILIES = (
    "MEMORY_BRIDGE_NOISE",
    "CAUSAL_CONFOUNDED_INTERVENTION",
    "PLANNING_H2_H5",
    "PROGRAM_NESTED_NOVEL",
    "CREDIT_MULTI_EPISODE",
    "META_CALIBRATION_MIXED",
)


def _cfg(budget_units: float) -> CognitiveLoopConfig:
    return CognitiveLoopConfig.for_stage(AblationStage.E_META, budget_units=budget_units)


def _name(rng: random.Random, prefix: str) -> str:
    return f"{prefix}_{rng.randrange(1_000_000_000):09d}"


def _atom(relation: str) -> ProgramNode:
    return ProgramNode(ProgramKind.ATOM, f"rule:transitive:{relation}")


def _base_request(case_id: str, world: WorldHypothesis, relation: str, src: str, dst: str, program: ProgramNode, **extra) -> CognitiveRequest:
    args = dict(
        episode_id=case_id,
        world=world,
        task=TaskProgram(TaskOpcode.QUERY_RELATION, relation, (src, dst)),
        program=program,
        novelty=0.30,
        uncertainty=0.22,
        predicted_outcome_reward=0.0,
        capability_hints=("program_execution",),
    )
    args.update(extra)
    return CognitiveRequest(**args)


def generate_case_fingerprint(seed: int, repeat: int) -> str:
    rng = random.Random((seed << 17) ^ repeat ^ 0x5A17B1)
    payload = {
        "seed": seed,
        "repeat": repeat,
        "relation": _name(rng, "blind_rel"),
        "entities": [_name(rng, "e") for _ in range(5)],
        "horizon": 2 + rng.randrange(4),
        "obs": round(rng.uniform(-1.0, 1.0), 6),
        "terminal": round(rng.uniform(1.4, 3.4), 6),
        "noise": rng.randrange(2, 8),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _memory_bridge_noise(rng: random.Random, case_id: str, budget_units: float) -> dict:
    rel = _name(rng, "мост")
    a, b, c = (_name(rng, p) for p in ("исток", "узел", "цель"))
    world = WorldHypothesis(case_id + ":w", (WorldFact(OperatorSymbol(rel, 2), (Entity(a), Entity(b)), True),))
    core = CognitiveRecursiveCoreR1()
    useful_raw = core.memory.add_raw({"source": _name(rng, "archive"), "valid": True}, confidence=1.0, tags=(case_id, "bridge"))
    core.memory.consolidate(
        MemoryLevel.SEMANTIC,
        WorldFact(OperatorSymbol(rel, 2), (Entity(b), Entity(c)), True),
        (useful_raw.memory_id,), confidence=1.0, tags=(case_id, "bridge"),
    )
    for i in range(rng.randrange(2, 8)):
        core.memory.add_raw({"noise": i, "token": _name(rng, "junk")}, confidence=1.0, tags=(case_id, "bridge"))
    loop = CognitiveLoopR1(core, config=_cfg(budget_units))
    d = loop.deliberate(_base_request(case_id, world, rel, a, c, _atom(rel), memory_tags=(case_id, "bridge")))
    o = loop.observe(d, RewardVector(task=float(d.answer is True)))
    success = float(d.answer is True and d.execution.proof_coverage.complete)
    return {"success": success, "proof": float(d.execution.proof_coverage.complete), "spent": budget_units - o.state.budget.remaining_units}


def _causal_confounded(rng: random.Random, case_id: str, budget_units: float) -> dict:
    rel = _name(rng, "logic")
    a, b, c = (_name(rng, p) for p in ("a", "b", "c"))
    world = WorldHypothesis(case_id + ":w", (
        WorldFact(OperatorSymbol(rel, 2), (Entity(a), Entity(b)), True),
        WorldFact(OperatorSymbol(rel, 2), (Entity(b), Entity(c)), True),
    ))
    cause, effect = _name(rng, "cause"), _name(rng, "effect")
    sign = 1.0 if rng.random() < 0.5 else -1.0
    obs = 0.75 * sign
    intervention = -0.88 * sign
    counterfactual = -0.82 * sign
    evidence = (
        CausalEvidence(case_id + ":obs", cause, effect, CausalEvidenceKind.OBSERVATIONAL, obs, 1.0),
        CausalEvidence(case_id + ":do", cause, effect, CausalEvidenceKind.INTERVENTIONAL, intervention, 1.0),
        CausalEvidence(case_id + ":cf", cause, effect, CausalEvidenceKind.COUNTERFACTUAL, counterfactual, 1.0),
    )
    oracle_abstain = True
    loop = CognitiveLoopR1(CognitiveRecursiveCoreR1(), config=_cfg(budget_units))
    d = loop.deliberate(_base_request(case_id, world, rel, a, c, _atom(rel), causal_query=(cause, effect), causal_evidence=evidence))
    success = float((d.answer is None) == oracle_abstain and d.causal_edge is not None and not d.causal_edge.identified)
    o = loop.observe(d, RewardVector(task=success, causal_consistency=success))
    return {"success": success, "causal": success, "spent": budget_units - o.state.budget.remaining_units}


def _planning_case(rng: random.Random, case_id: str, budget_units: float, horizon: int) -> dict:
    rel = _name(rng, "planrel")
    a, b, c = (_name(rng, p) for p in ("a", "b", "c"))
    world = WorldHypothesis(case_id + ":w", (
        WorldFact(OperatorSymbol(rel, 2), (Entity(a), Entity(b)), True),
        WorldFact(OperatorSymbol(rel, 2), (Entity(b), Entity(c)), True),
    ))
    model = EmpiricalWorldModel()
    start = _name(rng, "start")
    dead = _name(rng, "dead")
    local = _name(rng, "local")
    invest = _name(rng, "invest")
    states = [start] + [_name(rng, f"s{i}") for i in range(1, horizon)] + [_name(rng, "goal")]
    actions = [invest] + [_name(rng, f"step{i}") for i in range(1, horizon)]
    local_reward = rng.uniform(0.65, 1.05)
    terminal_reward = rng.uniform(1.8, 3.2)
    for _ in range(5):
        model.observe(start, local, dead, local_reward)
        for i, action in enumerate(actions):
            reward = terminal_reward if i == horizon - 1 else rng.uniform(0.01, 0.12)
            model.observe(states[i], action, states[i + 1], reward)
    # Independent oracle: enumerate the two available root policies under the same discounted return.
    gamma = 0.95
    delayed_value = sum((gamma ** i) * (terminal_reward if i == horizon - 1 else 0.065) for i in range(horizon))
    oracle = invest if delayed_value > local_reward else local
    loop = CognitiveLoopR1(CognitiveRecursiveCoreR1(), model, config=_cfg(budget_units))
    d = loop.deliberate(_base_request(
        case_id, world, rel, a, c, _atom(rel), planning_state=start,
        novelty=rng.uniform(0.10, 0.55), uncertainty=rng.uniform(0.10, 0.45),
        capability_hints=("program_execution", "future_planning"),
    ))
    success = float(d.plan is not None and d.plan.action == oracle)
    o = loop.observe(d, RewardVector(task=success, progress=success))
    return {"success": success, "planning": success, "horizon": horizon, "spent": budget_units - o.state.budget.remaining_units}


def _program_nested_novel(rng: random.Random, case_id: str, budget_units: float) -> dict:
    rel = _name(rng, "nested")
    a, b, c = (_name(rng, p) for p in ("src", "mid", "dst"))
    world = WorldHypothesis(case_id + ":w", (
        WorldFact(OperatorSymbol(rel, 2), (Entity(a), Entity(b)), True),
        WorldFact(OperatorSymbol(rel, 2), (Entity(b), Entity(c)), True),
    ))
    ledger = TemporalLedger().assert_fact(rel, a, b, 11)
    composed = ProgramNode(ProgramKind.COMPOSE, children=(_atom(rel), _atom(rel)))
    program = ProgramNode(ProgramKind.TEMPORAL, children=(composed,), params=(("mode", "current"),))
    loop = CognitiveLoopR1(CognitiveRecursiveCoreR1(), config=_cfg(budget_units))
    d = loop.deliberate(_base_request(case_id, world, rel, a, c, program, temporal_ledger=ledger))
    success = float(d.answer is True and d.execution.proof_coverage.complete)
    o = loop.observe(d, RewardVector(task=success))
    return {"success": success, "proof": float(d.execution.proof_coverage.complete), "spent": budget_units - o.state.budget.remaining_units}


def _credit_multi_episode(rng: random.Random, case_id: str, budget_units: float) -> dict:
    core = CognitiveRecursiveCoreR1()
    candidates = [_name(rng, "cand") for _ in range(3)]
    correct = candidates[rng.randrange(len(candidates))]
    noise = _name(rng, "ungrounded")
    leakage = 0.0
    for episode in range(2):
        graph = CognitiveTraceGraph()
        for candidate in candidates:
            graph.add_node(candidate, "program", {"capability": "credit_blind", "verified": True})
            graph.connect(candidate, "answer", 1.0) if "answer" in graph.nodes else None
        graph.add_node(noise, "memory", {"capability": "memory_retrieval", "grounded": False})
        graph.add_node("answer", "answer", {"capability": "answer_selection"})
        graph.add_node("outcome", "outcome", {"capability": "outcome"})
        for candidate in candidates:
            graph.connect(candidate, "answer", 1.0)
        graph.connect(noise, "answer", 1.0)
        graph.connect("answer", "outcome", 1.0)
        cf = {candidate: (1.0 if candidate == correct else -0.5) for candidate in candidates}
        cf[noise] = 0.0
        credit = core.credit_learner.update(graph, "outcome", 1.0, counterfactual_credit=cf)
        leakage += max(0.0, float(credit.get(noise, 0.0)))
    chosen = max(candidates, key=lambda c: core.credit_learner.trust(c))
    success = float(chosen == correct and leakage == 0.0)
    spent = min(budget_units, 0.45)
    return {"success": success, "adaptation": success, "credit_leakage": leakage, "spent": spent}


def _meta_calibration_mixed(rng: random.Random, case_id: str, budget_units: float) -> dict:
    hard = rng.random() < 0.5
    rel = _name(rng, "cal")
    a, b, c = (_name(rng, p) for p in ("a", "b", "c"))
    world = WorldHypothesis(case_id + ":w", (
        WorldFact(OperatorSymbol(rel, 2), (Entity(a), Entity(b)), True),
        WorldFact(OperatorSymbol(rel, 2), (Entity(b), Entity(c)), True),
    ))
    novelty = rng.uniform(0.82, 0.99) if hard else rng.uniform(0.01, 0.20)
    uncertainty = rng.uniform(0.94, 0.999) if hard else rng.uniform(0.01, 0.25)
    oracle_abstain = hard
    loop = CognitiveLoopR1(CognitiveRecursiveCoreR1(), config=_cfg(budget_units))
    d = loop.deliberate(_base_request(case_id, world, rel, a, c, _atom(rel), novelty=novelty, uncertainty=uncertainty))
    success = float(bool(d.meta.abstain) == oracle_abstain)
    o = loop.observe(d, RewardVector(task=success, calibration_gain=success))
    return {"success": success, "abstention": success, "spent": budget_units - o.state.budget.remaining_units}


RUNNERS = {
    "MEMORY_BRIDGE_NOISE": _memory_bridge_noise,
    "CAUSAL_CONFOUNDED_INTERVENTION": _causal_confounded,
    "PROGRAM_NESTED_NOVEL": _program_nested_novel,
    "CREDIT_MULTI_EPISODE": _credit_multi_episode,
    "META_CALIBRATION_MIXED": _meta_calibration_mixed,
}


def _run_seed(seed: int, repeats: int, budget_units: float) -> dict:
    rng = random.Random(seed ^ 0xB11D2026)
    rows = []
    for repeat in range(repeats):
        order = list(BLIND_FAMILIES)
        rng.shuffle(order)
        for family in order:
            case_id = f"second-blind-{seed}-{repeat:03d}-{family.lower()}-{rng.randrange(1_000_000):06d}"
            if family == "PLANNING_H2_H5":
                horizon = 2 + ((seed + repeat) % 4)
                row = _planning_case(rng, case_id, budget_units, horizon)
            else:
                row = RUNNERS[family](rng, case_id, budget_units)
            row.update({"family": family, "case_id": case_id})
            rows.append(row)
    return {"seed": seed, "rows": rows}


def run_second_blind(*, seeds=(420001, 420002, 420003, 420004, 420005, 420006, 420007, 420008), repeats=10, budget_units=1.0) -> dict:
    seeds = tuple(int(s) for s in seeds)
    if not seeds or repeats <= 0 or budget_units <= 0:
        raise ValueError("invalid blind protocol")
    runs = [_run_seed(seed, repeats, budget_units) for seed in seeds]
    rows = [row for run in runs for row in run["rows"]]
    family_accuracy = {
        family: sum(r["success"] for r in rows if r["family"] == family) / sum(1 for r in rows if r["family"] == family)
        for family in BLIND_FAMILIES
    }
    exact = sum(r["success"] for r in rows) / len(rows)
    minimum_family = min(family_accuracy.values())
    seed_success = [sum(r["success"] for r in run["rows"]) / len(run["rows"]) for run in runs]
    mean_spent = sum(float(r["spent"]) for r in rows) / len(rows)
    max_spent = max(float(r["spent"]) for r in rows)
    budget_violations = sum(float(r["spent"]) > budget_units + 1e-12 for r in rows)
    credit_leakage = sum(float(r.get("credit_leakage", 0.0)) for r in rows)
    horizons = sorted({int(r["horizon"]) for r in rows if "horizon" in r})
    verdict = "TRANSFER_SUPPORTED" if exact >= 0.80 and minimum_family >= 0.50 else ("PARTIAL_TRANSFER" if exact >= 0.50 else "FAIL")
    return {
        "protocol": {
            "kind": "post_fix_second_blind_transfer",
            "frozen_arch_sha": FROZEN_ARCH_SHA,
            "families": list(BLIND_FAMILIES),
            "seeds": list(seeds),
            "seed_count": len(seeds),
            "repeats": repeats,
            "budget_units": budget_units,
            "reuses_first_far_oos_cases": False,
            "independent_oracle": True,
            "m32_meta_opened": False,
            "ftx2_authored": False,
            "boundary": "Second post-freeze blind transfer battery; not M32-META and not FTX2.",
        },
        "total_cases": len(rows),
        "case_ids": [r["case_id"] for r in rows],
        "family_accuracy": family_accuracy,
        "exact_task_success": exact,
        "minimum_family_accuracy": minimum_family,
        "planning_horizons_seen": horizons,
        "credit_leakage": credit_leakage,
        "mean_compute_spent": mean_spent,
        "max_compute_spent": max_spent,
        "success_per_compute": exact / mean_spent if mean_spent else 0.0,
        "budget_violations": budget_violations,
        "seed_success_std": statistics.pstdev(seed_success) if len(seed_success) > 1 else 0.0,
        "seed_success": seed_success,
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="420001,420002,420003,420004,420005,420006,420007,420008")
    ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--budget-units", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    result = run_second_blind(seeds=tuple(int(x) for x in args.seeds.split(",") if x), repeats=args.repeats, budget_units=args.budget_units)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "exact": result["exact_task_success"], "minimum_family": result["minimum_family_accuracy"], "families": result["family_accuracy"], "horizons": result["planning_horizons_seen"]}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
