from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class CognitiveIR:
    plan: str
    target: str | None = None
    subject: str | None = None
    relation: str | None = None
    object: str | None = None
    operands: tuple[int,...] = ()
    timeline: tuple[str,...] = ()
    relevant: tuple[str,...] = ()
    distractors: tuple[str,...] = ()
    metadata: dict[str,Any] = field(default_factory=dict)
