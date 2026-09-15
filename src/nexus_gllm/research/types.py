from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class SearchQuery:
    text: str
    mode: str='PROBE'
    freshness_days: int|None=None
    domain: str|None=None
    top_k: int=10

@dataclass(frozen=True)
class SearchHit:
    engine: str
    url: str
    title: str
    snippet: str
    score: float=0.0
    published_at: str|None=None
    source_type: str='web'
    metadata: dict[str,Any]=field(default_factory=dict)

@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    url: str
    title: str
    content_hash: str
    source_type: str
    reliability: float
    independence_group: str
    published_at: str|None=None
    retrieved_at: str|None=None
    content: str=''

@dataclass(frozen=True)
class ClaimProposal:
    claim_id: str
    subject: str
    relation: str
    object: str
    claim_text: str
    support_span: str
    source_id: str
    extractor_confidence: float

@dataclass(frozen=True)
class ResearchNeed:
    query: str
    importance: float=1.0
    novelty: float=1.0
    expected_gain: float=1.0
    cost: float=1.0
    latency: float=0.0
    risk: float=0.0

@dataclass(frozen=True)
class ClaimDecision:
    status: str
    score: float
    support: float
    contradiction: float
