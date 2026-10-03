from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexus_gllm.unified_v3.cognitive.ablation import AblationStage, CognitiveLoopConfig, FROZEN_COMPUTE_COSTS
from nexus_gllm.unified_v3.cognitive.causal_model import CausalEvidence, CausalEvidenceKind
from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1, CognitiveRequest
from nexus_gllm.unified_v3.cognitive.memory import MemoryLevel
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.cognitive.reward import RewardVector
from nexus_gllm.unified_v3.cognitive.runtime import CognitiveRecursiveCoreR1
from nexus_gllm.unified_v3.cognitive.world_model import EmpiricalWorldModel
from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, TaskOpcode, TaskProgram, WorldFact, WorldHypothesis


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
    # Deliberately retrieved but not admissible as proof evidence. It tests that
    # credit selectivity does not reward mere graph proximity.
    core.memory.add_raw({"distractor": True}, confidence=1.0, tags=("chain",))
    return core


def _world_model() -> EmpiricalWorldModel:
    model = EmpiricalWorldModel()
    for _ in range(3):
        model.observe("s0", "advance", "s1", 0.6)
        model.observe("s1", "finish", "s2", 1.0)
        model.observe("s0", "stall", "s0", -0.2)
    return model


def _request(case_id: str, *, hard: bool) -> CognitiveRequest:
    world = WorldHypothesis(
        "equal-budget-world:" + case_id,
        (WorldFact(OperatorSymbol("r", 2), (Entity("a"), Entity("b")), True),),
    )
    return CognitiveRequest(
        episode_id=case_id,
        world=world,
        task=TaskProgram(TaskOpcode.QUERY_RELATION, "r", ("a", "c")),
        program=ProgramNode(ProgramKind.ATOM, "rule:transitive:r"),
        memory_tags=("chain",),
        causal_query=("x", "y"),
        causal_evidence=(
            CausalEvidence(case_id + ":i", "x", "y", CausalEvidenceKind.INTERVENTIONAL, 0.90, 0.95),
            CausalEvidence(case_id + ":cf", "x", "y", CausalEvidenceKind.COUNTERFACTUAL, 0.82, 0.90),
        ),
        planning_state="s0",
        novelty=0.88 if hard else 0.10,
        uncertainty=0.84 if hard else 0.12,
        predicted_outcome_reward=0.0,
        capability_hints=("program_execution",),
    )


def _case_ids(seed: int, repeats: int) -> tuple[tuple[str, bool], ...]:
    if repeats <= 0:
        raise ValueError("repeats must be positive")
    return tuple(
        (f"dev-{seed}-{i:03d}-{'hard' if hard else 'easy'}", hard)
        for i in range(repeats)
        for hard in (False, True)
    )


def _credit_eligible(decision, node_id: str) -> bool:
    node = decision.trace_graph.nodes[node_id]
    payload = node.payload if isinstance(node.payload, dict) else {}
    if node.kind == "program":
        return bool(payload.get("verified", True))
    if node.kind == "memory":
        return bool(payload.get("grounded", True))
    if node.kind == "meta":
        return bool(payload.get("adaptive", True))
    if node.kind == "causal":
        return bool(payload.get("identified", True))
    return True


def _run_stage(stage: AblationStage, cases, *, budget_units: float) -> dict:
    sums = {
        "answer": 0.0,
        "proof_complete": 0.0,
        "memory_grounding": 0.0,
        "causal_identification": 0.0,
        "planning_correct": 0.0,
        "adaptive_meta": 0.0,
    }
    eligible_positive = 0.0
    all_positive = 0.0
    ineligible_positive = 0.0
    compute_spent = []
    violations = 0
    ids = []

    for case_id, hard in cases:
        ids.append(case_id)
        config = CognitiveLoopConfig.for_stage(stage, budget_units=budget_units)
        loop = CognitiveLoopR1(_core_with_memory(), _world_model(), config=config)
        decision = loop.deliberate(_request(case_id, hard=hard))
        outcome = loop.observe(decision, RewardVector(task=1.0))

        sums["answer"] += float(decision.answer is True)
        sums["proof_complete"] += float(decision.execution.proof_coverage.complete)
        sums["memory_grounding"] += float(any(event.kind == "memory_grounding" for event in decision.state.trace))
        sums["causal_identification"] += float(decision.causal_edge is not None and decision.causal_edge.identified)
        sums["planning_correct"] += float(decision.plan is not None and decision.plan.action == "advance")
        sums["adaptive_meta"] += float(decision.meta.reason != "fixed_ablation_policy")

        spent = budget_units - outcome.state.budget.remaining_units
        compute_spent.append(spent)
        if spent > budget_units + 1e-12:
            violations += 1

        for node_id, value in outcome.credit.items():
            if node_id in {"answer", "outcome"} or value <= 0.0:
                continue
            all_positive += value
            if _credit_eligible(decision, node_id):
                eligible_positive += value
            else:
                ineligible_positive += value

    n = float(len(cases))
    return {
        "episodes": len(cases),
        "case_ids": ids,
        "answer_accuracy": sums["answer"] / n,
        "proof_complete_rate": sums["proof_complete"] / n,
        "memory_grounding_rate": sums["memory_grounding"] / n,
        "causal_identification_rate": sums["causal_identification"] / n,
        "planning_action_accuracy": sums["planning_correct"] / n,
        "credit_eligible_precision": eligible_positive / all_positive if all_positive > 0 else 0.0,
        "ineligible_positive_credit_mass": ineligible_positive,
        "adaptive_meta_rate": sums["adaptive_meta"] / n,
        "mean_compute_spent": sum(compute_spent) / n,
        "max_compute_spent": max(compute_spent),
        "budget_violations": violations,
    }


def run_benchmark(*, seed: int = 1701, repeats: int = 16, budget_units: float = 1.0) -> dict:
    if budget_units <= 0:
        raise ValueError("budget_units must be positive")
    cases = _case_ids(seed, repeats)
    stages = {
        stage.value: _run_stage(stage, cases, budget_units=budget_units)
        for stage in AblationStage
    }
    all_ids = [tuple(stage["case_ids"]) for stage in stages.values()]
    return {
        "protocol": {
            "kind": "controlled_dev_cumulative_ablation",
            "seed": seed,
            "repeats": repeats,
            "budget_units": budget_units,
            "frozen_cost_schedule": FROZEN_COMPUTE_COSTS.__dict__,
            "same_case_ids_across_stages": len(set(all_ids)) == 1,
            "final_transfer_evidence": False,
            "scientific_boundary": "Controlled DEV cumulative organ ablation. This is executable architecture evidence, not FAR-OOS, META, or FTX2 transfer evidence.",
        },
        "stages": stages,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1701)
    parser.add_argument("--repeats", type=int, default=16)
    parser.add_argument("--budget-units", type=float, default=1.0)
    parser.add_argument("--out")
    args = parser.parse_args()
    result = run_benchmark(seed=args.seed, repeats=args.repeats, budget_units=args.budget_units)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
