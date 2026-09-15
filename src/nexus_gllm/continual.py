from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionMetrics:
    baseline_new: float
    candidate_new: float
    baseline_legacy: float
    candidate_legacy: float
    protected_exact: float
    invalid_mutation_rate: float

    @property
    def new_gain(self) -> float:
        return self.candidate_new - self.baseline_new

    @property
    def legacy_drop(self) -> float:
        return self.baseline_legacy - self.candidate_legacy


@dataclass(frozen=True)
class PromotionDecision:
    promote: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ContinualLearningReport:
    decision: PromotionDecision
    metrics: PromotionMetrics
    candidate_checkpoint: str | None = None
    promoted_checkpoint: str | None = None
    rollback_checkpoint: str | None = None
    gradient_steps: int = 0


class PromotionGate:
    def __init__(self, *, min_new_gain: float = 0.02, max_legacy_drop: float = 0.01) -> None:
        self.min_new_gain = float(min_new_gain)
        self.max_legacy_drop = float(max_legacy_drop)

    def decide(self, metrics: PromotionMetrics) -> PromotionDecision:
        reasons: list[str] = []
        if metrics.new_gain < self.min_new_gain:
            reasons.append("insufficient_new_gain")
        if metrics.legacy_drop > self.max_legacy_drop:
            reasons.append("legacy_regression")
        if metrics.protected_exact < 1.0:
            reasons.append("protected_exact")
        if metrics.invalid_mutation_rate != 0.0:
            reasons.append("invalid_mutation_rate")
        return PromotionDecision(promote=not reasons, reasons=tuple(reasons))
