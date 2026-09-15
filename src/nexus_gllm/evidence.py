from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable


@dataclass(frozen=True)
class EvidenceRecord:
    id: str
    proposition_key: tuple[str, str, str]
    polarity: str
    source_id: str
    source_reliability: float
    confidence: float
    sequence_index: int | None
    provenance: str

    @classmethod
    def create(
        cls,
        *,
        proposition_key: tuple[str, str, str],
        polarity: str,
        source_id: str,
        source_reliability: float,
        confidence: float,
        sequence_index: int | None,
        provenance: str,
    ) -> "EvidenceRecord":
        if polarity not in {"support", "attack"}:
            raise ValueError("polarity must be support or attack")
        if not 0.0 <= float(source_reliability) <= 1.0:
            raise ValueError("source_reliability must be within [0,1]")
        if not 0.0 <= float(confidence) <= 1.0:
            raise ValueError("confidence must be within [0,1]")
        if len(proposition_key) != 3 or not all(str(v) for v in proposition_key):
            raise ValueError("proposition_key must contain relation, subject and object")
        payload = {
            "proposition_key": list(proposition_key),
            "polarity": polarity,
            "source_id": source_id,
            "source_reliability": round(float(source_reliability), 12),
            "confidence": round(float(confidence), 12),
            "sequence_index": sequence_index,
            "provenance": provenance,
        }
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        evidence_id = "evd_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
        return cls(
            id=evidence_id,
            proposition_key=tuple(str(v) for v in proposition_key),
            polarity=polarity,
            source_id=str(source_id),
            source_reliability=float(source_reliability),
            confidence=float(confidence),
            sequence_index=sequence_index,
            provenance=str(provenance),
        )


class EvidenceLedger:
    def __init__(self) -> None:
        self._records: dict[str, EvidenceRecord] = {}

    def add(self, record: EvidenceRecord) -> EvidenceRecord:
        if record.id in self._records:
            raise ValueError(f"duplicate evidence: {record.id}")
        self._records[record.id] = record
        return record

    def get(self, evidence_id: str) -> EvidenceRecord:
        return self._records[evidence_id]

    def values(self) -> tuple[EvidenceRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def for_proposition(self, proposition_key: tuple[str, str, str]) -> tuple[EvidenceRecord, ...]:
        key = tuple(proposition_key)
        return tuple(record for record in self.values() if record.proposition_key == key)

    def __len__(self) -> int:
        return len(self._records)
