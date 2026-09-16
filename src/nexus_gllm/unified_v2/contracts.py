from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Any

@dataclass(frozen=True)
class TextTurn:
    turn_id: str
    text_ru: str
    speaker: Literal['user','assistant','system']='user'
    timestamp: float|None=None

@dataclass(frozen=True)
class EntityRef:
    entity_id: str
    canonical_name: str
    surface_forms: tuple[str,...]=()

@dataclass(frozen=True)
class ClaimProposal:
    claim_id: str
    subject: EntityRef
    relation: str
    object: EntityRef|str|float|bool
    confidence: float
    provenance: tuple[str,...]
    polarity: Literal['positive','negative']='positive'

@dataclass(frozen=True)
class Claim:
    claim_id: str
    subject: EntityRef
    relation: str
    object: EntityRef|str|float|bool
    confidence: float
    provenance: tuple[str,...]
    authority: str
    polarity: Literal['positive','negative']='positive'

@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source_id: str
    supports: tuple[str,...]=()
    contradicts: tuple[str,...]=()
    trust: float=0.5
    content_hash: str=''

@dataclass(frozen=True)
class AnswerGraph:
    claims: tuple[Claim,...]=()
    required_citations: tuple[str,...]=()
    uncertainty: tuple[str,...]=()
    abstentions: tuple[str,...]=()

@dataclass(frozen=True)
class TraceEvent:
    kind: Literal['call','bypass','commit','reject']
    organ_id: str
    detail: str

@dataclass(frozen=True)
class ExecutionTrace:
    events: tuple[TraceEvent,...]
