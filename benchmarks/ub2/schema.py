from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class SemanticContract:
    required_claims: tuple[str, ...] = ()
    forbidden_claims: tuple[str, ...] = ()
    required_citations: tuple[str, ...] = ()
    clarification_required: bool = False
    expected_uncertainty: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class UB2Case:
    case_id: str
    track: str
    prompt: str
    history: tuple[str, ...]
    contract: SemanticContract
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            'case_id': self.case_id,
            'track': self.track,
            'prompt': self.prompt,
            'history': list(self.history),
            'contract': self.contract.to_dict(),
            'metadata': self.metadata,
        }

@dataclass(frozen=True)
class EvidenceDocument:
    doc_id: str
    source_family: str
    text: str
    independent_group: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
