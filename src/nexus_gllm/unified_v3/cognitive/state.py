from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class ComputeBudget:
    remaining_units: float = 1.0
    max_depth: int = 3
    max_fanout: int = 4
    max_experts: int = 3
    max_memory_records: int = 16
    max_planning_expansions: int = 64
    max_planning_depth: int = 12

    def spend(self, units: float) -> "ComputeBudget":
        if units < 0:
            raise ValueError("compute spend must be non-negative")
        return replace(self, remaining_units=max(0.0, self.remaining_units - float(units)))


@dataclass(frozen=True)
class CognitiveTraceEvent:
    step: int
    kind: str
    ref_id: str | None = None
    data: tuple[tuple[str, Any], ...] = ()


@dataclass(frozen=True)
class NexusCognitiveState:
    episode_id: str
    step: int = 0
    world_id: str | None = None
    belief_ids: tuple[str, ...] = ()
    memory_ids: tuple[str, ...] = ()
    program_ids: tuple[str, ...] = ()
    branch_id: str | None = None
    predicted_reward: float = 0.0
    observed_reward: float | None = None
    uncertainty: float = 1.0
    novelty: float = 0.0
    budget: ComputeBudget = field(default_factory=ComputeBudget)
    trace: tuple[CognitiveTraceEvent, ...] = ()

    def transition(self, kind: str, *, ref_id: str | None = None, data: dict[str, Any] | None = None, **changes) -> "NexusCognitiveState":
        next_step = self.step + 1
        ev = CognitiveTraceEvent(next_step, kind, ref_id, tuple(sorted((data or {}).items())))
        return replace(self, step=next_step, trace=self.trace + (ev,), **changes)
