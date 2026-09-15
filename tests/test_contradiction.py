from nexus_gllm.belief import BeliefGraph, BeliefKey
from nexus_gllm.contradiction import ContradictionEngine
from nexus_gllm.evidence import EvidenceLedger, EvidenceRecord
from nexus_gllm.source_reliability import SourceRegistry
from nexus_gllm.graph import DynamicHyperGraph
from nexus_gllm.temporal import EventGraphReasoner


def _support(graph, key, seq):
    graph.observe(EvidenceRecord.create(
        proposition_key=key.as_tuple(),
        polarity="support",
        source_id=f"src-{seq}",
        source_reliability=0.95,
        confidence=0.95,
        sequence_index=seq,
        provenance="test",
    ))


def test_owned_by_different_objects_form_explicit_contradiction_set():
    beliefs = BeliefGraph(EvidenceLedger(), SourceRegistry())
    a = BeliefKey("owned_by", "car", "anton")
    b = BeliefKey("owned_by", "car", "boris")
    _support(beliefs, a, 1)
    _support(beliefs, b, 2)
    engine = ContradictionEngine(beliefs)
    found = engine.detect()
    assert len(found) == 1
    assert set(found[0].belief_keys) == {a, b}
    assert found[0].schema == "functional_relation"


def test_nonexclusive_relation_does_not_create_object_conflict():
    beliefs = BeliefGraph(EvidenceLedger(), SourceRegistry())
    _support(beliefs, BeliefKey("is_a", "x", "class-a"), 1)
    _support(beliefs, BeliefKey("is_a", "x", "class-b"), 2)
    assert ContradictionEngine(beliefs).detect() == ()


def test_temporal_cycle_candidate_is_rejected_by_existing_reasoner():
    graph = DynamicHyperGraph()
    reasoner = EventGraphReasoner(graph)
    a = reasoner.ensure_event("A")
    b = reasoner.ensure_event("B")
    reasoner.add_before(a, b)
    try:
        reasoner.add_before(b, a)
    except ValueError as exc:
        assert "cycle" in str(exc)
    else:
        raise AssertionError("temporal cycle must be rejected")
