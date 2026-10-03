from nexus_gllm.unified_v3.cognitive.ablation import AblationStage, CognitiveLoopConfig
from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1, CognitiveRequest
from nexus_gllm.unified_v3.cognitive.causal_model import CausalEvidence, CausalEvidenceKind
from nexus_gllm.unified_v3.cognitive.memory import MemoryLevel
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.cognitive.reward import RewardVector
from nexus_gllm.unified_v3.cognitive.runtime import CognitiveRecursiveCoreR1
from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, TaskOpcode, TaskProgram, WorldFact, WorldHypothesis


def _core_with_memory():
    core = CognitiveRecursiveCoreR1()
    raw = core.memory.add_raw({"source": "obs"}, confidence=1.0, tags=("chain",))
    core.memory.consolidate(
        MemoryLevel.SEMANTIC,
        WorldFact(OperatorSymbol("r", 2), (Entity("b"), Entity("c"))),
        (raw.memory_id,),
        confidence=1.0,
        tags=("chain",),
    )
    return core


def _request():
    world = WorldHypothesis(
        "ablation-world",
        (WorldFact(OperatorSymbol("r", 2), (Entity("a"), Entity("b"))),),
    )
    return CognitiveRequest(
        episode_id="ablation-episode",
        world=world,
        task=TaskProgram(TaskOpcode.QUERY_RELATION, "r", ("a", "c")),
        program=ProgramNode(ProgramKind.ATOM, "rule:transitive:r"),
        memory_tags=("chain",),
        causal_query=("x", "y"),
        causal_evidence=(
            CausalEvidence("i", "x", "y", CausalEvidenceKind.INTERVENTIONAL, 0.9, 0.95),
            CausalEvidence("cf", "x", "y", CausalEvidenceKind.COUNTERFACTUAL, 0.8, 0.9),
        ),
        novelty=0.8,
        uncertainty=0.8,
    )


def test_ablation_stages_are_strictly_cumulative_under_one_budget_contract():
    expected = {
        AblationStage.A_MEMORY: (True, False, False, False, False),
        AblationStage.B_CAUSAL: (True, True, False, False, False),
        AblationStage.C_FUTURE: (True, True, True, False, False),
        AblationStage.D_CREDIT: (True, True, True, True, False),
        AblationStage.E_META: (True, True, True, True, True),
    }

    configs = {stage: CognitiveLoopConfig.for_stage(stage, budget_units=1.0) for stage in AblationStage}
    for stage, config in configs.items():
        assert (
            config.enable_memory,
            config.enable_causal,
            config.enable_future,
            config.enable_credit,
            config.enable_meta,
        ) == expected[stage]
        assert config.budget_units == 1.0
        assert config.costs.total_declared > 0

    cost_schedules = {config.costs for config in configs.values()}
    assert len(cost_schedules) == 1


def test_stage_a_does_not_silently_execute_causal_future_credit_or_adaptive_meta():
    config = CognitiveLoopConfig.for_stage(AblationStage.A_MEMORY, budget_units=1.0)
    loop = CognitiveLoopR1(_core_with_memory(), config=config)
    decision = loop.deliberate(_request())

    kinds = {event.kind for event in decision.state.trace}
    assert "memory_grounding" in kinds
    assert "causal_inference" not in kinds
    assert "future_plan" not in kinds
    assert decision.causal_edge is None
    assert decision.answer is True
    assert decision.meta.reason == "fixed_ablation_policy"

    ledger = decision.compute
    assert ledger.budget_units == 1.0
    assert ledger.spent_units > 0
    assert ledger.spent_units <= ledger.budget_units
    assert set(ledger.by_module) <= {"memory", "program"}

    before = loop.core.self_model.snapshot()
    outcome = loop.observe(decision, reward=RewardVector(task=1.0))
    assert outcome.credit == {}
    assert loop.core.self_model.snapshot() == before


def test_stage_b_adds_causal_under_same_budget_and_records_compute_by_module():
    config = CognitiveLoopConfig.for_stage(AblationStage.B_CAUSAL, budget_units=1.0)
    loop = CognitiveLoopR1(_core_with_memory(), config=config)
    decision = loop.deliberate(_request())

    kinds = {event.kind for event in decision.state.trace}
    assert "memory_grounding" in kinds
    assert "causal_inference" in kinds
    assert "future_plan" not in kinds
    assert decision.causal_edge is not None
    assert decision.causal_edge.identified is True
    assert decision.meta.reason == "fixed_ablation_policy"
    assert set(decision.compute.by_module) <= {"memory", "causal", "program"}
    assert decision.compute.spent_units <= 1.0
