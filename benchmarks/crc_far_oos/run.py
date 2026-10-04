from __future__ import annotations

import argparse
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
from nexus_gllm.unified_v3.contracts import Entity, FactVersion, OperatorSymbol, TaskOpcode, TaskProgram, WorldFact, WorldHypothesis
from nexus_gllm.unified_v3.temporal import TemporalLedger


FROZEN_ARCH_SHA = "6067746d3dbab7a5a0a7388545b73116fd23c25a"
FAR_OOS_FAMILIES = (
    "MEMORY_CHAIN_RU",
    "TEMPORAL_SNAPSHOT",
    "CAUSAL_REVERSAL",
    "LONG_HORIZON_PLAN",
    "CREDIT_TRANSFER",
    "UNSEEN_COMPOSITION",
    "CALIBRATED_ABSTENTION",
)


def _atom(relation: str) -> ProgramNode:
    return ProgramNode(ProgramKind.ATOM, f"rule:transitive:{relation}")


def _full_config(budget_units: float) -> CognitiveLoopConfig:
    return CognitiveLoopConfig.for_stage(AblationStage.E_META, budget_units=budget_units)


def _relation(rng: random.Random, prefix: str) -> str:
    return f"{prefix}_{rng.randrange(10_000_000):07d}"


def _entity(rng: random.Random, prefix: str) -> str:
    return f"{prefix}_{rng.randrange(10_000_000):07d}"


def _request(case_id: str, world: WorldHypothesis, relation: str, src: str, dst: str, program: ProgramNode, **kwargs) -> CognitiveRequest:
    base = dict(
        episode_id=case_id,
        world=world,
        task=TaskProgram(TaskOpcode.QUERY_RELATION, relation, (src, dst)),
        program=program,
        novelty=0.22,
        uncertainty=0.18,
        predicted_outcome_reward=0.0,
        capability_hints=("program_execution",),
    )
    base.update(kwargs)
    return CognitiveRequest(**base)


def _memory_chain(rng: random.Random, case_id: str, budget_units: float) -> dict:
    rel = _relation(rng, "связь")
    a, b, c = (_entity(rng, x) for x in ("альфа", "бета", "гамма"))
    world = WorldHypothesis(case_id + ":world", (WorldFact(OperatorSymbol(rel, 2), (Entity(a), Entity(b)), True),))
    core = CognitiveRecursiveCoreR1()
    raw = core.memory.add_raw({"источник": "удаленный_архив", "case": case_id}, confidence=1.0, tags=(case_id, "память"))
    core.memory.consolidate(
        MemoryLevel.SEMANTIC,
        WorldFact(OperatorSymbol(rel, 2), (Entity(b), Entity(c)), True),
        (raw.memory_id,),
        confidence=1.0,
        tags=(case_id, "память"),
    )
    loop = CognitiveLoopR1(core, config=_full_config(budget_units))
    decision = loop.deliberate(_request(case_id, world, rel, a, c, _atom(rel), memory_tags=(case_id, "память")))
    outcome = loop.observe(decision, RewardVector(task=float(decision.answer is True)))
    success = float(decision.answer is True and decision.execution.proof_coverage.complete)
    return {"success": success, "proof": float(decision.execution.proof_coverage.complete), "spent": budget_units - outcome.state.budget.remaining_units}


def _temporal_snapshot(rng: random.Random, case_id: str, budget_units: float) -> dict:
    rel = _relation(rng, "route")
    x, old, new, target = (_entity(rng, p) for p in ("node", "old", "new", "target"))
    ledger = TemporalLedger().assert_fact(rel, x, old, 10).assert_fact(rel, x, new, 20, supersede=True)
    world = WorldHypothesis(
        case_id + ":world",
        (WorldFact(OperatorSymbol(rel, 2), (Entity(old), Entity(target)), True),),
    )
    program = ProgramNode(ProgramKind.TEMPORAL, children=(_atom(rel),), params=(("time", "15"),))
    loop = CognitiveLoopR1(CognitiveRecursiveCoreR1(), config=_full_config(budget_units))
    decision = loop.deliberate(_request(case_id, world, rel, x, target, program, temporal_ledger=ledger))
    outcome = loop.observe(decision, RewardVector(task=float(decision.answer is True)))
    success = float(decision.answer is True and decision.execution.proof_coverage.complete)
    return {"success": success, "proof": float(decision.execution.proof_coverage.complete), "spent": budget_units - outcome.state.budget.remaining_units}


def _causal_reversal(rng: random.Random, case_id: str, budget_units: float) -> dict:
    rel = _relation(rng, "edge")
    a, b, c = (_entity(rng, p) for p in ("u", "v", "w"))
    world = WorldHypothesis(case_id + ":world", (
        WorldFact(OperatorSymbol(rel, 2), (Entity(a), Entity(b)), True),
        WorldFact(OperatorSymbol(rel, 2), (Entity(b), Entity(c)), True),
    ))
    cause, effect = _entity(rng, "cause"), _entity(rng, "effect")
    evidence = (
        CausalEvidence(case_id + ":obs", cause, effect, CausalEvidenceKind.OBSERVATIONAL, 0.95, 1.0),
        CausalEvidence(case_id + ":do", cause, effect, CausalEvidenceKind.INTERVENTIONAL, -0.90, 1.0),
        CausalEvidence(case_id + ":cf", cause, effect, CausalEvidenceKind.COUNTERFACTUAL, -0.85, 1.0),
    )
    loop = CognitiveLoopR1(CognitiveRecursiveCoreR1(), config=_full_config(budget_units))
    decision = loop.deliberate(_request(case_id, world, rel, a, c, _atom(rel), causal_query=(cause, effect), causal_evidence=evidence))
    success = float(decision.answer is None and decision.causal_edge is not None and not decision.causal_edge.identified)
    outcome = loop.observe(decision, RewardVector(task=success, causal_consistency=success))
    return {"success": success, "causal": success, "spent": budget_units - outcome.state.budget.remaining_units}


def _planning_model(rng: random.Random) -> tuple[EmpiricalWorldModel, str, str]:
    model = EmpiricalWorldModel()
    s0, s1, s2, goal, dead = (_entity(rng, p) for p in ("s0", "s1", "s2", "goal", "dead"))
    local = _entity(rng, "local")
    invest = _entity(rng, "invest")
    advance = _entity(rng, "advance")
    finish = _entity(rng, "finish")
    for _ in range(5):
        model.observe(s0, local, dead, 0.92)
        model.observe(s0, invest, s1, 0.05)
        model.observe(s1, advance, s2, 0.10)
        model.observe(s2, finish, goal, 2.40)
    return model, s0, invest


def _long_horizon_plan(rng: random.Random, case_id: str, budget_units: float) -> dict:
    rel = _relation(rng, "rel")
    a, b, c = (_entity(rng, p) for p in ("a", "b", "c"))
    world = WorldHypothesis(case_id + ":world", (
        WorldFact(OperatorSymbol(rel, 2), (Entity(a), Entity(b)), True),
        WorldFact(OperatorSymbol(rel, 2), (Entity(b), Entity(c)), True),
    ))
    model, start, optimal = _planning_model(rng)
    loop = CognitiveLoopR1(CognitiveRecursiveCoreR1(), model, config=_full_config(budget_units))
    decision = loop.deliberate(_request(case_id, world, rel, a, c, _atom(rel), planning_state=start, novelty=0.35, uncertainty=0.25))
    success = float(decision.plan is not None and decision.plan.action == optimal and decision.plan.depth >= 3)
    outcome = loop.observe(decision, RewardVector(task=success, progress=success))
    return {"success": success, "planning": success, "spent": budget_units - outcome.state.budget.remaining_units}


def _credit_transfer(rng: random.Random, case_id: str, budget_units: float) -> dict:
    core = CognitiveRecursiveCoreR1()
    correct = _entity(rng, "candidate")
    wrong = _entity(rng, "candidate")
    distractor = _entity(rng, "memory_noise")
    before = correct if core.credit_learner.trust(correct) > core.credit_learner.trust(wrong) else wrong
    graph = CognitiveTraceGraph()
    graph.add_node(correct, "program", {"capability": "transfer_candidate", "verified": True})
    graph.add_node(wrong, "program", {"capability": "transfer_candidate", "verified": True})
    graph.add_node(distractor, "memory", {"capability": "memory_retrieval", "grounded": False})
    graph.add_node("answer", "answer", {"capability": "answer_selection"})
    graph.add_node("outcome", "outcome", {"capability": "outcome"})
    graph.connect(correct, "answer", 1.0)
    graph.connect(wrong, "answer", 1.0)
    graph.connect(distractor, "answer", 1.0)
    graph.connect("answer", "outcome", 1.0)
    credit = core.credit_learner.update(graph, "outcome", 1.0, counterfactual_credit={correct: 1.0, wrong: -1.0, distractor: 0.0})
    after = correct if core.credit_learner.trust(correct) > core.credit_learner.trust(wrong) else wrong
    leakage = max(0.0, float(credit.get(distractor, 0.0)))
    success = float(before != correct and after == correct and leakage == 0.0)
    spent = 0.35
    if spent > budget_units + 1e-12:
        raise RuntimeError("credit transfer exceeded budget")
    return {"success": success, "adaptation": success, "credit_leakage": leakage, "spent": spent}


def _unseen_composition(rng: random.Random, case_id: str, budget_units: float) -> dict:
    rel = _relation(rng, "compose")
    a, b, c = (_entity(rng, p) for p in ("src", "mid", "dst"))
    world = WorldHypothesis(case_id + ":world", (
        WorldFact(OperatorSymbol(rel, 2), (Entity(a), Entity(b)), True),
        WorldFact(OperatorSymbol(rel, 2), (Entity(b), Entity(c)), True),
    ))
    primitive = _atom(rel)
    temporal = ProgramNode(ProgramKind.TEMPORAL, children=(primitive,), params=(("mode", "current"),))
    program = ProgramNode(ProgramKind.COMPOSE, children=(primitive, temporal))
    ledger = TemporalLedger().assert_fact(rel, a, b, 5)
    loop = CognitiveLoopR1(CognitiveRecursiveCoreR1(), config=_full_config(budget_units))
    decision = loop.deliberate(_request(case_id, world, rel, a, c, program, temporal_ledger=ledger))
    success = float(decision.answer is True and decision.execution.proof_coverage.complete and len(decision.execution.steps) >= 4)
    outcome = loop.observe(decision, RewardVector(task=success))
    return {"success": success, "proof": float(decision.execution.proof_coverage.complete), "spent": budget_units - outcome.state.budget.remaining_units}


def _calibrated_abstention(rng: random.Random, case_id: str, budget_units: float) -> dict:
    rel = _relation(rng, "uncertain")
    a, b, c = (_entity(rng, p) for p in ("a", "b", "c"))
    world = WorldHypothesis(case_id + ":world", (
        WorldFact(OperatorSymbol(rel, 2), (Entity(a), Entity(b)), True),
        WorldFact(OperatorSymbol(rel, 2), (Entity(b), Entity(c)), True),
    ))
    loop = CognitiveLoopR1(CognitiveRecursiveCoreR1(), config=_full_config(budget_units))
    decision = loop.deliberate(_request(case_id, world, rel, a, c, _atom(rel), novelty=0.99, uncertainty=0.995))
    success = float(decision.meta.abstain)
    outcome = loop.observe(decision, RewardVector(task=success, calibration_gain=success))
    return {"success": success, "abstention": success, "spent": budget_units - outcome.state.budget.remaining_units}


RUNNERS = {
    "MEMORY_CHAIN_RU": _memory_chain,
    "TEMPORAL_SNAPSHOT": _temporal_snapshot,
    "CAUSAL_REVERSAL": _causal_reversal,
    "LONG_HORIZON_PLAN": _long_horizon_plan,
    "CREDIT_TRANSFER": _credit_transfer,
    "UNSEEN_COMPOSITION": _unseen_composition,
    "CALIBRATED_ABSTENTION": _calibrated_abstention,
}


def _run_seed(seed: int, repeats: int, budget_units: float) -> dict:
    rng = random.Random(seed)
    rows = []
    for repeat in range(repeats):
        order = list(FAR_OOS_FAMILIES)
        rng.shuffle(order)
        for family in order:
            case_id = f"far-{seed}-{repeat:03d}-{family.lower()}-{rng.randrange(1_000_000):06d}"
            row = dict(RUNNERS[family](rng, case_id, budget_units))
            row.update({"family": family, "case_id": case_id})
            rows.append(row)
    return {"seed": seed, "rows": rows}


def run_far_oos(*, seeds: tuple[int, ...] = (91001, 91002, 91003, 91004, 91005), repeats: int = 8, budget_units: float = 1.0) -> dict:
    if not seeds:
        raise ValueError("seeds must not be empty")
    if repeats <= 0:
        raise ValueError("repeats must be positive")
    if budget_units <= 0:
        raise ValueError("budget_units must be positive")
    runs = [_run_seed(seed, repeats, budget_units) for seed in seeds]
    rows = [row for run in runs for row in run["rows"]]
    family_accuracy = {
        family: sum(r["success"] for r in rows if r["family"] == family) / sum(1 for r in rows if r["family"] == family)
        for family in FAR_OOS_FAMILIES
    }
    exact = sum(r["success"] for r in rows) / len(rows)
    mean_spent = sum(float(r["spent"]) for r in rows) / len(rows)
    seed_success = [sum(r["success"] for r in run["rows"]) / len(run["rows"]) for run in runs]
    minimum_family = min(family_accuracy.values())
    verdict = "TRANSFER_SUPPORTED" if exact >= 0.80 and minimum_family >= 0.50 else ("PARTIAL_TRANSFER" if exact >= 0.50 else "FAIL")
    proof_rows = [r for r in rows if "proof" in r]
    causal_rows = [r for r in rows if "causal" in r]
    planning_rows = [r for r in rows if "planning" in r]
    adaptation_rows = [r for r in rows if "adaptation" in r]
    abstention_rows = [r for r in rows if "abstention" in r]
    return {
        "protocol": {
            "kind": "frozen_far_oos_transfer",
            "frozen_arch_sha": FROZEN_ARCH_SHA,
            "seed_count": len(seeds),
            "seeds": list(seeds),
            "repeats": repeats,
            "budget_units": budget_units,
            "families": FAR_OOS_FAMILIES,
            "uses_controlled_dev_generator": False,
            "m32_meta_opened": False,
            "ftx2_authored": False,
            "scientific_boundary": "Fresh post-freeze FAR-OOS evaluator. Not M32-META and not FTX2.",
        },
        "case_ids": [r["case_id"] for r in rows],
        "total_cases": len(rows),
        "family_accuracy": family_accuracy,
        "exact_task_success": exact,
        "proof_complete_rate": sum(r["proof"] for r in proof_rows) / len(proof_rows),
        "causal_accuracy": sum(r["causal"] for r in causal_rows) / len(causal_rows),
        "planning_accuracy": sum(r["planning"] for r in planning_rows) / len(planning_rows),
        "post_feedback_transfer": sum(r["adaptation"] for r in adaptation_rows) / len(adaptation_rows),
        "calibrated_abstention": sum(r["abstention"] for r in abstention_rows) / len(abstention_rows),
        "credit_leakage": sum(float(r.get("credit_leakage", 0.0)) for r in rows),
        "mean_compute_spent": mean_spent,
        "max_compute_spent": max(float(r["spent"]) for r in rows),
        "success_per_compute": exact / mean_spent if mean_spent > 0 else 0.0,
        "budget_violations": sum(float(r["spent"]) > budget_units + 1e-12 for r in rows),
        "seed_success": seed_success,
        "seed_success_std": statistics.pstdev(seed_success),
        "verdict": verdict,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="91001,91002,91003,91004,91005")
    parser.add_argument("--repeats", type=int, default=8)
    parser.add_argument("--budget-units", type=float, default=1.0)
    parser.add_argument("--out")
    args = parser.parse_args()
    seeds = tuple(int(x.strip()) for x in args.seeds.split(",") if x.strip())
    result = run_far_oos(seeds=seeds, repeats=args.repeats, budget_units=args.budget_units)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
