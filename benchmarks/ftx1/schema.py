from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FTXCase:
    case_id: str
    track: str
    prompt: str
    history: tuple[str, ...] = ()
    documents: tuple[tuple[str, str], ...] = ()
    pair_group: str | None = None

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            'case_id': self.case_id,
            'prompt': self.prompt,
            'history': list(self.history),
            'documents': [{'id': doc_id, 'text': text} for doc_id, text in self.documents],
        }


@dataclass(frozen=True)
class FTXGold:
    answer: str | None = None
    structured: tuple[str, ...] = ()
    epistemic: str | None = None
    abstain: bool = False
    citations: tuple[str, ...] = ()
    semantic_key: str | None = None
    audit: tuple[tuple[str, str], ...] = ()

    def audit_dict(self) -> dict[str, str]:
        return dict(self.audit)


@dataclass(frozen=True)
class FTXPrediction:
    answer: str | None = None
    structured: tuple[str, ...] = ()
    epistemic: str | None = None
    abstain: bool = False
    citations: tuple[str, ...] = ()


@dataclass(frozen=True)
class CaseScore:
    strict: bool
    answer_ok: bool
    structured_ok: bool
    epistemic_ok: bool
    abstain_ok: bool
    citations_ok: bool


@dataclass(frozen=True)
class TrackScore:
    track: str
    correct: int
    total: int

    @property
    def strict(self) -> float:
        return self.correct / self.total if self.total else 0.0


@dataclass(frozen=True)
class SuiteScore:
    full_strict: float
    macro_strict: float
    tracks: tuple[TrackScore, ...] = field(default_factory=tuple)
