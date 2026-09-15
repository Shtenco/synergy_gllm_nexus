from nexus_gllm.belief import BeliefGraph, BeliefKey
from nexus_gllm.evidence import EvidenceLedger, EvidenceRecord
from nexus_gllm.source_reliability import SourceRegistry


def _evidence(key, polarity, confidence=0.9, reliability=0.9, seq=1):
    return EvidenceRecord.create(
        proposition_key=key.as_tuple(),
        polarity=polarity,
        source_id=f"src-{seq}",
        source_reliability=reliability,
        confidence=confidence,
        sequence_index=seq,
        provenance="test",
    )


def test_support_only_belief_becomes_active_without_gradient_steps():
    ledger = EvidenceLedger()
    registry = SourceRegistry()
    graph = BeliefGraph(ledger=ledger, sources=registry)
    key = BeliefKey("owned_by", "car", "anton")
    update = graph.observe(_evidence(key, "support", 0.99, 0.99))
    assert update.snapshot.status == "active"
    assert update.snapshot.posterior >= 0.75
    assert update.gradient_steps == 0


def test_attack_only_belief_becomes_retracted():
    graph = BeliefGraph(EvidenceLedger(), SourceRegistry())
    key = BeliefKey("located_in", "x", "y")
    update = graph.observe(_evidence(key, "attack", 0.99, 0.99))
    assert update.snapshot.status == "retracted"
    assert update.snapshot.posterior <= 0.25


def test_mixed_support_and_attack_is_disputed():
    graph = BeliefGraph(EvidenceLedger(), SourceRegistry())
    key = BeliefKey("is_a", "x", "class-a")
    graph.observe(_evidence(key, "support", 0.95, 0.95, 1))
    update = graph.observe(_evidence(key, "attack", 0.95, 0.95, 2))
    assert update.snapshot.status == "disputed"
    assert update.snapshot.support_evidence_ids
    assert update.snapshot.attack_evidence_ids
    assert 0.0 <= update.snapshot.posterior <= 1.0


def test_query_missing_belief_returns_unknown_prior():
    graph = BeliefGraph(EvidenceLedger(), SourceRegistry())
    snapshot = graph.get(BeliefKey("owned_by", "missing", "nobody"))
    assert snapshot.status == "unknown"
    assert snapshot.posterior == 0.5
