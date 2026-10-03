from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from nexus_gllm.unified_v3.cognitive.ablation import AblationStage, CognitiveLoopConfig, FROZEN_COMPUTE_COSTS
from nexus_gllm.unified_v3.cognitive.causal_model import CausalEvidence, CausalEvidenceKind
from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1, CognitiveRequest
from nexus_gllm.unified_v3.cognitive.credit import CognitiveTraceGraph
from nexus_gllm.unified_v3.cognitive.memory import MemoryLevel
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.cognitive.reward import RewardVector
from nexus_gllm.unified_v3.cognitive.runtime import CognitiveRecursiveCoreR1
from nexus_gllm.unified_v3.cognitive.world_model import EmpiricalWorldModel
from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, TaskOpcode, TaskProgram, WorldFact, WorldHypothesis


FAMILIES = (
    "MEMORY_REQUIRED",
    "CAUSAL_TRAP",
    "FUTURE_TRAP",
    "CREDIT_LEARNING",
    "META_RESOURCE",
)


def _core_with_memory() -> CognitiveRecursiveCoreR1:
    core = CognitiveRecursiveCoreR1()
    raw = core.memory.add_raw({"source": "controlled-observation"}, confidence=1.0, tags=("chain",))
    core.memory.consolidate(
        MemoryLevel.SEMANTIC,
        WorldFact(OperatorSymbol("r", 2), (Entity("b"), Entity("c")), True),
        (raw.memory_id,),
        confidence=1.0,
        tags=("chain",),
    )
    # Retrieved but non-groundable distractor: useful for measuring credit leakage.
    core.memory.add_raw({"distractor": True}, confidence=1.0, tags=("chain",))
    return core


def _base_world(case_id: str) -> WorldHypothesis:
    return WorldHypothesis(
        "discriminative-world:" + case_id,
        (WorldFact(OperatorSymbol("r", 2), (Entity("a"), Entity("b")), True),),
    )


def _base_request(case_id: str, **kwargs) -> CognitiveRequest:
    defaults = dict(
        episode_id=case_id,
        world=_base_world(case_id),
        task=TaskProgram(TaskOpcode.QUERY_RELATION, "r", ("a", "c")),
        program=ProgramNode(ProgramKind.ATOM, "rule:transitive:r"),
        memory_tags=("chain",),
        novelty=0.10,
        uncertainty=0.12,
        predicted_outcome_reward=0.0,
        capability_hints=("program_execution",),
    )
    defaults.update(kwargs)
    return CognitiveRequest(**defaults)


def _future_trap_model() -> EmpiricalWorldModel:
    """Greedy cash_now wins immediately; invest wins only after rollout."""
    model = EmpiricalWorldModel()
    for _ in range(4):
        model.observe("s0", "cash_now", "dead", 0.80)
        model.observe("s0", "invest", "s1", 0.10)
        model.observe("s1", "finish", "goal", 2.00)
    return model


def _spent(decision, outcome, budget_units: float) -> float:
    return budget_units - outcome.state.budget.remaining_units


def _memory_required(stage: AblationStage, case_id: str, budget_units: float) -> dict:
    config = CognitiveLoopConfig.for_stage(stage, budget_units=budget_units)
    loop = CognitiveLoopR1(_core_with_memory(), config=config)
    decision = loop.deliberate(_base_request(case_id))
    outcome = loop.observe(decision, RewardVector(task=float(decision.answer is True)))

    # Counterfactual control: same task/stage, but no memory evidence exists.
    control = CognitiveLoopR1(CognitiveRecursiveCoreR1(), config=config)
    control_decision = control.deliberate(_base_request(case_id + ":no-memory"))
    success = float(decision.answer is True and decision.execution.proof_coverage.complete)
    control_success = float(control_decision.answer is True and control_decision.execution.proof_coverage.complete)
    return {
        "success": success,
        "spent": _spent(decision, outcome, budget_units),
        "proof": float(decision.execution.proof_coverage.complete),
        "memory_necessity": max(0.0, success - control_success),
    }


def _causal_trap(stage: AblationStage, case_id: str, budget_units: float) -> dict:
    """Strong correlation says yes; intervention+counterfactual contradiction says not identified."""
    config = CognitiveLoopConfig.for_stage(stage, budget_units=budget_units)
    request = _base_request(
        case_id,
        causal_query=("x", "y"),
        causal_evidence=(
            CausalEvidence(case_id + ":obs", "x", "y", CausalEvidenceKind.OBSERVATIONAL, 1.0, 1.0),
            CausalEvidence(case_id + ":do", "x", "y", CausalEvidenceKind.INTERVENTIONAL, -1.0, 1.0),
            CausalEvidence(case_id + ":cf", "x", "y", CausalEvidenceKind.COUNTERFACTUAL, -1.0, 1.0),
        ),
    )
    loop = CognitiveLoopR1(_core_with_memory(), config=config)
    decision = loop.deliberate(request)
    # Correct final behavior is abstention: causal effect is not identified once
    # experimental/counterfactual evidence contradicts observational correlation.
    success = float(decision.answer is None)
    outcome = loop.observe(decision, RewardVector(task=success, causal_consistency=success))
    return {
        "success": success,
        "spent": _spent(decision, outcome, budget_units),
        "causal": success,
    }


def _future_trap(stage: AblationStage, case_id: str, budget_units: float) -> dict:
    config = CognitiveLoopConfig.for_stage(stage, budget_units=budget_units)
    request = _base_request(case_id, planning_state="s0")
    loop = CognitiveLoopR1(_core_with_memory(), _future_trap_model(), config=config)
    decision = loop.deliberate(request)
    # Without future planning the operational fallback is the locally-greedy action.
    action = decision.plan.action if decision.plan is not None else "cash_now"
    success = float(action == "invest")
    outcome = loop.observe(decision, RewardVector(task=success, progress=success))
    return {
        "success": success,
        "spent": _spent(decision, outcome, budget_units),
        "planning": success,
    }


def _credit_learning(stage: AblationStage, case_id: str, budget_units: float) -> dict:
    """Episode N feedback must change the candidate chosen in episode N+1."""
    config = CognitiveLoopConfig.for_stage(stage, budget_units=budget_units)
    core = CognitiveRecursiveCoreR1()
    safe = "candidate:safe"
    risky = "candidate:risky"
    distractor = "memory:ungrounded"

    before_safe = core.credit_learner.trust(safe)
    before_risky = core.credit_learner.trust(risky)
    before_choice = risky if before_risky >= before_safe else safe  # deterministic bad tie-break

    positive_leak = 0.0
    if config.enable_credit:
        graph = CognitiveTraceGraph()
        graph.add_node(safe, "program", {"capability": "candidate_safe", "verified": True})
        graph.add_node(risky, "program", {"capability": "candidate_risky", "verified": True})
        graph.add_node(distractor, "memory", {"capability": "memory_retrieval", "grounded": False})
        graph.add_node("answer", "answer", {"capability": "answer_selection"})
        graph.add_node("outcome", "outcome", {"capability": "outcome"})
        graph.connect(safe, "answer", 1.0)
        graph.connect(risky, "answer", 1.0)
        graph.connect(distractor, "answer", 1.0)
        graph.connect("answer", "outcome", 1.0)
        credit = core.credit_learner.update(
            graph,
            "outcome",
            1.0,
            counterfactual_credit={safe: 1.0, risky: -1.0, distractor: 0.0},
        )
        positive_leak = sum(max(0.0, v) for k, v in credit.items() if k == distractor)

    after_safe = core.credit_learner.trust(safe)
    after_risky = core.credit_learner.trust(risky)
    after_choice = safe if after_safe > after_risky else risky
    success = float(after_choice == safe)
    adaptation = float(before_choice != after_choice and after_choice == safe)

    # One feedback episode uses program execution plus recursive credit when enabled.
    spent = FROZEN_COMPUTE_COSTS.program
    if config.enable_credit:
        spent += FROZEN_COMPUTE_COSTS.credit
    if config.enable_meta:
        spent += FROZEN_COMPUTE_COSTS.meta
    if spent > budget_units + 1e-12:
        raise RuntimeError("credit-learning case exceeded budget")
    return {
        "success": success,
        "spent": spent,
        "adaptation": adaptation,
        "credit_leakage": positive_leak,
    }


def _meta_resource(stage: AblationStage, case_id: str, budget_units: float, hard: bool) -> dict:
    config = CognitiveLoopConfig.for_stage(stage, budget_units=budget_units)
    request = _base_request(
        case_id,
        novelty=0.95 if hard else 0.05,
        uncertainty=0.98 if hard else 0.08,
    )
    loop = CognitiveLoopR1(_core_with_memory(), config=config)
    decision = loop.deliberate(request)
    # Easy: answer. Hard: calibrated abstention is the correct behavior.
    success = float(decision.meta.abstain if hard else (not decision.meta.abstain and decision.answer is True))
    calibrated = float(decision.meta.abstain == hard)
    outcome = loop.observe(decision, RewardVector(task=success, calibration_gain=calibrated))
    return {
        "success": success,
        "spent": _spent(decision, outcome, budget_units),
        "abstention": calibrated,
    }


def _case_ids(seed: int, repeats: int) -> tuple[tuple[str, str, bool], ...]:
    if repeats <= 0:
        raise ValueError("repeats must be positive")
    cases = []
    for i in range(repeats):
        for family in FAMILIES:
            if family == "META_RESOURCE":
                for hard in (False, True):
                    cases.append((f"dev-{seed}-{i:03d}-{family}-{'hard' if hard else 'easy'}", family, hard))
            else:
                cases.append((f"dev-{seed}-{i:03d}-{family}", family, False))
    return tuple(cases)


def _run_stage(stage: AblationStage, cases, *, budget_units: float) -> dict:
    successes = []
    spent = []
    family_values = {family: [] for family in FAMILIES}
    proof = []
    causal = []
    planning = []
    adaptation = []
    abstention = []
    necessity = []
    leakage = 0.0
    ids = []

    for case_id, family, hard in cases:
        ids.append(case_id)
        if family == "MEMORY_REQUIRED":
            row = _memory_required(stage, case_id, budget_units)
            proof.append(row["proof"])
            necessity.append(row["memory_necessity"])
        elif family == "CAUSAL_TRAP":
            row = _causal_trap(stage, case_id, budget_units)
            causal.append(row["causal"])
        elif family == "FUTURE_TRAP":
            row = _future_trap(stage, case_id, budget_units)
            planning.append(row["planning"])
        elif family == "CREDIT_LEARNING":
            row = _credit_learning(stage, case_id, budget_units)
            adaptation.append(row["adaptation"])
            leakage += row["credit_leakage"]
        else:
            row = _meta_resource(stage, case_id, budget_units, hard)
            abstention.append(row["abstention"])

        value = float(row["success"])
        family_values[family].append(value)
        successes.append(value)
        spent.append(float(row["spent"]))

    mean_success = sum(successes) / len(successes)
    mean_spent = sum(spent) / len(spent)
    return {
        "episodes": len(cases),
        "case_ids": ids,
        "family_accuracy": {k: sum(v) / len(v) for k, v in family_values.items()},
        "exact_task_success": mean_success,
        "multi_step_proof_success": sum(proof) / len(proof),
        "causal_trap_accuracy": sum(causal) / len(causal),
        "long_horizon_planning_accuracy": sum(planning) / len(planning),
        "post_feedback_adaptation": sum(adaptation) / len(adaptation),
        "calibrated_abstention": sum(abstention) / len(abstention),
        "memory_necessity_delta": sum(necessity) / len(necessity),
        "credit_leakage": leakage,
        "mean_compute_spent": mean_spent,
        "max_compute_spent": max(spent),
        "success_per_compute": mean_success / mean_spent if mean_spent > 0 else 0.0,
        "budget_violations": sum(x > budget_units + 1e-12 for x in spent),
    }


def _single_seed(seed: int, repeats: int, budget_units: float) -> dict:
    cases = _case_ids(seed, repeats)
    stages = {stage.value: _run_stage(stage, cases, budget_units=budget_units) for stage in AblationStage}
    exact = {name: data["exact_task_success"] for name, data in stages.items()}
    names = [stage.value for stage in AblationStage]
    deltas = {f"{b}-{a}": exact[b] - exact[a] for a, b in zip(names, names[1:])}
    all_ids = [tuple(stage["case_ids"]) for stage in stages.values()]
    return {
        "protocol": {
            "kind": "controlled_dev_discriminative_cumulative_ablation",
            "seed": seed,
            "repeats": repeats,
            "budget_units": budget_units,
            "families": FAMILIES,
            "frozen_cost_schedule": FROZEN_COMPUTE_COSTS.__dict__,
            "same_case_ids_across_stages": len(set(all_ids)) == 1,
            "final_transfer_evidence": False,
            "scientific_boundary": "Controlled DEV mixed-task cumulative ablation. Behavioral architecture evidence only; not FAR-OOS, META, or FTX2 transfer evidence.",
        },
        "stages": stages,
        "deltas": deltas,
    }


def run_benchmark(*, seed: int = 1701, repeats: int = 16, budget_units: float = 1.0) -> dict:
    if budget_units <= 0:
        raise ValueError("budget_units must be positive")
    result = _single_seed(seed, repeats, budget_units)
    result["stability"] = {
        "seed_count": 1,
        "seeds": [seed],
        "per_stage_success_std": {stage.value: 0.0 for stage in AblationStage},
    }
    return result


def run_multi_seed_benchmark(*, seeds: tuple[int, ...], repeats: int = 16, budget_units: float = 1.0) -> dict:
    if not seeds:
        raise ValueError("seeds must not be empty")
    runs = [_single_seed(seed, repeats, budget_units) for seed in seeds]
    stage_names = [stage.value for stage in AblationStage]
    aggregate = runs[0]
    aggregate["protocol"] = dict(aggregate["protocol"])
    aggregate["protocol"]["seed"] = None
    aggregate["protocol"]["seeds"] = list(seeds)
    aggregate["protocol"]["same_case_ids_across_stages"] = all(r["protocol"]["same_case_ids_across_stages"] for r in runs)

    numeric_keys = (
        "exact_task_success", "multi_step_proof_success", "causal_trap_accuracy",
        "long_horizon_planning_accuracy", "post_feedback_adaptation", "calibrated_abstention",
        "memory_necessity_delta", "credit_leakage", "mean_compute_spent", "max_compute_spent",
        "success_per_compute", "budget_violations",
    )
    stages = {}
    for name in stage_names:
        rows = [r["stages"][name] for r in runs]
        family_accuracy = {
            family: sum(row["family_accuracy"][family] for row in rows) / len(rows)
            for family in FAMILIES
        }
        stage = {key: sum(float(row[key]) for row in rows) / len(rows) for key in numeric_keys}
        stage["episodes"] = sum(row["episodes"] for row in rows)
        stage["case_ids"] = [case_id for row in rows for case_id in row["case_ids"]]
        stage["family_accuracy"] = family_accuracy
        stage["budget_violations"] = int(sum(row["budget_violations"] for row in rows))
        stage["max_compute_spent"] = max(row["max_compute_spent"] for row in rows)
        stages[name] = stage
    aggregate["stages"] = stages
    aggregate["deltas"] = {
        f"{b}-{a}": stages[b]["exact_task_success"] - stages[a]["exact_task_success"]
        for a, b in zip(stage_names, stage_names[1:])
    }
    aggregate["stability"] = {
        "seed_count": len(seeds),
        "seeds": list(seeds),
        "per_stage_success_std": {
            name: statistics.pstdev(r["stages"][name]["exact_task_success"] for r in runs)
            for name in stage_names
        },
    }
    return aggregate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1701)
    parser.add_argument("--seeds", help="comma-separated deterministic DEV seeds")
    parser.add_argument("--repeats", type=int, default=16)
    parser.add_argument("--budget-units", type=float, default=1.0)
    parser.add_argument("--out")
    args = parser.parse_args()
    if args.seeds:
        seeds = tuple(int(x.strip()) for x in args.seeds.split(",") if x.strip())
        result = run_multi_seed_benchmark(seeds=seeds, repeats=args.repeats, budget_units=args.budget_units)
    else:
        result = run_benchmark(seed=args.seed, repeats=args.repeats, budget_units=args.budget_units)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
