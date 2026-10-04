from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AblationStage(str, Enum):
    A_MEMORY = "A_MEMORY"
    B_CAUSAL = "B_CAUSAL"
    C_FUTURE = "C_FUTURE"
    D_CREDIT = "D_CREDIT"
    E_META = "E_META"


@dataclass(frozen=True)
class ComputeCosts:
    """Frozen normalized compute schedule for CRC cumulative ablations.

    Units are protocol accounting units, not wall-clock seconds or FLOPs. The
    same schedule is shared by every stage; a benchmark may change the common
    budget cap, but never a stage-specific module price.
    """

    memory: float = 0.10
    program: float = 0.20
    causal: float = 0.15
    future: float = 0.25
    credit: float = 0.15
    meta: float = 0.10

    @property
    def total_declared(self) -> float:
        return self.memory + self.program + self.causal + self.future + self.credit + self.meta

    def for_module(self, module: str) -> float:
        if module not in {"memory", "program", "causal", "future", "credit", "meta"}:
            raise KeyError(module)
        return float(getattr(self, module))


FROZEN_COMPUTE_COSTS = ComputeCosts()


@dataclass(frozen=True)
class ComputeLedger:
    budget_units: float
    entries: tuple[tuple[str, float], ...] = ()

    @property
    def spent_units(self) -> float:
        return sum(units for _, units in self.entries)

    @property
    def remaining_units(self) -> float:
        return max(0.0, float(self.budget_units) - self.spent_units)

    @property
    def by_module(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for module, units in self.entries:
            out[module] = out.get(module, 0.0) + float(units)
        return out

    def spend(self, module: str, units: float) -> "ComputeLedger":
        units = float(units)
        if units < 0:
            raise ValueError("compute spend must be non-negative")
        if self.spent_units + units > float(self.budget_units) + 1e-12:
            raise RuntimeError(
                f"compute budget exceeded by {module}: "
                f"{self.spent_units + units:.6f}>{self.budget_units:.6f}"
            )
        return ComputeLedger(self.budget_units, self.entries + ((module, units),))


@dataclass(frozen=True)
class CognitiveLoopConfig:
    stage: AblationStage | None = None
    enable_memory: bool = True
    enable_causal: bool = True
    enable_future: bool = True
    enable_credit: bool = True
    enable_meta: bool = True
    budget_units: float = 1.0
    costs: ComputeCosts = FROZEN_COMPUTE_COSTS

    def __post_init__(self) -> None:
        if self.budget_units <= 0:
            raise ValueError("budget_units must be positive")
        if self.costs.total_declared <= 0:
            raise ValueError("compute cost schedule must be positive")

    @classmethod
    def for_stage(cls, stage: AblationStage, *, budget_units: float = 1.0) -> "CognitiveLoopConfig":
        rank = {
            AblationStage.A_MEMORY: 0,
            AblationStage.B_CAUSAL: 1,
            AblationStage.C_FUTURE: 2,
            AblationStage.D_CREDIT: 3,
            AblationStage.E_META: 4,
        }[stage]
        return cls(
            stage=stage,
            enable_memory=True,
            enable_causal=rank >= 1,
            enable_future=rank >= 2,
            enable_credit=rank >= 3,
            enable_meta=rank >= 4,
            budget_units=float(budget_units),
            costs=FROZEN_COMPUTE_COSTS,
        )

    @classmethod
    def full(cls, *, budget_units: float = 1.0) -> "CognitiveLoopConfig":
        """Backward-compatible full CRC configuration outside ablation runs."""
        return cls(stage=None, budget_units=float(budget_units))
