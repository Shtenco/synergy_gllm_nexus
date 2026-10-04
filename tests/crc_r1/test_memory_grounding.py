from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1, CognitiveRequest
from nexus_gllm.unified_v3.cognitive.memory import MemoryLevel
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.cognitive.runtime import CognitiveRecursiveCoreR1
from nexus_gllm.unified_v3.contracts import (
    Entity,
    OperatorSymbol,
    TaskOpcode,
    TaskProgram,
    WorldFact,
    WorldHypothesis,
)


def _request(memory_tags=()):
    relation = OperatorSymbol("r", 2)
    world = WorldHypothesis(
        "memory-grounding-world",
        (WorldFact(relation, (Entity("a"), Entity("b"))),),
    )
    return CognitiveRequest(
        episode_id="memory-grounding-episode",
        world=world,
        task=TaskProgram(TaskOpcode.QUERY_RELATION, "r", ("a", "c")),
        program=ProgramNode(ProgramKind.ATOM, "rule:transitive:r"),
        memory_tags=tuple(memory_tags),
        novelty=0.2,
        uncertainty=0.2,
    )


def test_provenance_backed_semantic_memory_can_ground_missing_world_fact():
    relation = OperatorSymbol("r", 2)
    remembered_fact = WorldFact(relation, (Entity("b"), Entity("c")))

    core = CognitiveRecursiveCoreR1()
    raw = core.memory.add_raw(
        {"source": "observation-1", "relation": "r", "src": "b", "dst": "c"},
        confidence=1.0,
        tags=("chain",),
    )
    semantic = core.memory.consolidate(
        MemoryLevel.SEMANTIC,
        remembered_fact,
        (raw.memory_id,),
        confidence=1.0,
        tags=("chain",),
    )

    without_memory = CognitiveLoopR1(CognitiveRecursiveCoreR1()).deliberate(_request())
    with_memory = CognitiveLoopR1(core).deliberate(_request(("chain",)))

    assert without_memory.execution.execution.truth is None
    assert with_memory.execution.execution.truth is True
    assert with_memory.answer is True
    assert semantic.memory_id in with_memory.state.memory_ids
    assert with_memory.execution.world_id == "memory-grounding-world:memory"

    grounding_events = [event for event in with_memory.state.trace if event.kind == "memory_grounding"]
    assert len(grounding_events) == 1
    grounding_data = dict(grounding_events[0].data)
    assert grounding_data["accepted_fact_count"] == 1
    assert grounding_data["accepted_memory_ids"] == (semantic.memory_id,)


def test_raw_memory_never_becomes_world_authority():
    relation = OperatorSymbol("r", 2)
    raw_fact = WorldFact(relation, (Entity("b"), Entity("c")))

    core = CognitiveRecursiveCoreR1()
    raw = core.memory.add_raw(raw_fact, confidence=1.0, tags=("chain",))

    decision = CognitiveLoopR1(core).deliberate(_request(("chain",)))

    assert raw.memory_id in decision.state.memory_ids
    assert decision.execution.execution.truth is None
    assert decision.answer is None
    assert decision.execution.world_id == "memory-grounding-world"
    assert not [event for event in decision.state.trace if event.kind == "memory_grounding"]
