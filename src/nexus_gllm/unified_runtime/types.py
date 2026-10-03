from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class CortexDecisionFeatures:
    plan_probs: Tuple[float, ...]
    relation_probs: Tuple[float, ...]
    role_probs: Tuple[float, ...]
    temporal_probs: Tuple[float, ...]
    plan_entropy: float
    relation_entropy: float
    role_entropy: float
    temporal_entropy: float
    uncertainty: float
    checkpoint_sha256: str
    checkpoint_name: str
    reconstruction_nhead: int
    reconstruction_exact_source: bool

@dataclass(frozen=True)
class LearnedMetaDecision:
    expert_top_k: int
    branch_depth: int
    branch_fanout: int
    memory_limit: int
    verification_level: int
    action_index: int
    action_probs: Tuple[float, ...]
    value_estimate: float
    uncertainty: float
