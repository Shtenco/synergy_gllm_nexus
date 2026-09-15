from nexus_gllm.evidence import EvidenceLedger, EvidenceRecord
from nexus_gllm.source_reliability import SourceRegistry


def test_evidence_ids_are_deterministic_and_duplicates_rejected():
    record = EvidenceRecord.create(
        proposition_key=("owned_by", "car", "anton"),
        polarity="support",
        source_id="source-a",
        source_reliability=0.8,
        confidence=0.9,
        sequence_index=1,
        provenance="test",
    )
    same = EvidenceRecord.create(
        proposition_key=("owned_by", "car", "anton"),
        polarity="support",
        source_id="source-a",
        source_reliability=0.8,
        confidence=0.9,
        sequence_index=1,
        provenance="test",
    )
    assert record.id == same.id
    ledger = EvidenceLedger()
    ledger.add(record)
    try:
        ledger.add(same)
    except ValueError as exc:
        assert "duplicate evidence" in str(exc)
    else:
        raise AssertionError("duplicate evidence must be rejected")


def test_source_reliability_uses_beta_updates_and_stays_bounded():
    registry = SourceRegistry()
    initial = registry.get("source-a")
    assert initial.alpha == 1.0
    assert initial.beta == 1.0
    assert initial.reliability == 0.5

    confirmed = registry.update("source-a", was_correct=True, weight=3.0)
    assert confirmed.alpha == 4.0
    assert confirmed.beta == 1.0
    assert 0.0 < confirmed.reliability < 1.0

    contradicted = registry.update("source-a", was_correct=False, weight=2.0)
    assert contradicted.alpha == 4.0
    assert contradicted.beta == 3.0
    assert 0.0 < contradicted.reliability < 1.0


def test_source_update_rejects_non_positive_weight():
    registry = SourceRegistry()
    for bad in (0.0, -1.0):
        try:
            registry.update("source-a", was_correct=True, weight=bad)
        except ValueError as exc:
            assert "weight" in str(exc)
        else:
            raise AssertionError("non-positive weight must fail")
