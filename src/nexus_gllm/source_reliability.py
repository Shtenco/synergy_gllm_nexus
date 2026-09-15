from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class SourceReliability:
    source_id: str
    alpha: float = 1.0
    beta: float = 1.0
    confirmations: float = 0.0
    contradictions: float = 0.0

    @property
    def reliability(self) -> float:
        total = self.alpha + self.beta
        if total <= 0.0:
            return 0.5
        return self.alpha / total


class SourceRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, SourceReliability] = {}

    def get(self, source_id: str) -> SourceReliability:
        source_id = str(source_id)
        if source_id not in self._sources:
            self._sources[source_id] = SourceReliability(source_id=source_id)
        return self._sources[source_id]

    def update(self, source_id: str, *, was_correct: bool, weight: float = 1.0) -> SourceReliability:
        weight = float(weight)
        if weight <= 0.0:
            raise ValueError("weight must be positive")
        current = self.get(source_id)
        if was_correct:
            updated = replace(
                current,
                alpha=current.alpha + weight,
                confirmations=current.confirmations + weight,
            )
        else:
            updated = replace(
                current,
                beta=current.beta + weight,
                contradictions=current.contradictions + weight,
            )
        self._sources[current.source_id] = updated
        return updated

    def values(self) -> tuple[SourceReliability, ...]:
        return tuple(self._sources[key] for key in sorted(self._sources))
