from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class StructuralEquation:
    variable: str
    parents: tuple[tuple[str, float], ...] = ()
    bias: float = 0.0


class LinearSCMOracle:
    """Small deterministic linear SCM used only as an independent evaluator.

    The production NEXUS causal engine is deliberately not called here.
    Values follow structural equations

        X := bias + sum(weight(parent) * parent) + U_X

    unless X is replaced by an explicit intervention do(X=value).
    """

    def __init__(self, equations: tuple[StructuralEquation, ...]):
        if not equations:
            raise ValueError("SCM requires at least one equation")
        self._eq = {eq.variable: eq for eq in equations}
        if len(self._eq) != len(equations):
            raise ValueError("duplicate structural variable")
        for eq in equations:
            for parent, _ in eq.parents:
                if parent not in self._eq:
                    raise ValueError(f"unknown parent {parent!r} for {eq.variable!r}")
        self._order = self._topological_order()

    def _topological_order(self) -> tuple[str, ...]:
        remaining = {name: {p for p, _ in eq.parents} for name, eq in self._eq.items()}
        out = []
        while remaining:
            ready = sorted(name for name, parents in remaining.items() if not parents)
            if not ready:
                raise ValueError("structural graph contains a directed cycle")
            for name in ready:
                out.append(name)
                remaining.pop(name)
            for parents in remaining.values():
                parents.difference_update(ready)
        return tuple(out)

    @property
    def variables(self) -> tuple[str, ...]:
        return self._order

    def evaluate(
        self,
        *,
        exogenous: Mapping[str, float] | None = None,
        interventions: Mapping[str, float] | None = None,
    ) -> dict[str, float]:
        exogenous = dict(exogenous or {})
        interventions = dict(interventions or {})
        unknown = set(interventions) - set(self._eq)
        if unknown:
            raise ValueError(f"unknown intervention variables: {sorted(unknown)!r}")
        values: dict[str, float] = {}
        for variable in self._order:
            if variable in interventions:
                values[variable] = float(interventions[variable])
                continue
            eq = self._eq[variable]
            value = float(eq.bias) + float(exogenous.get(variable, 0.0))
            for parent, weight in eq.parents:
                value += float(weight) * values[parent]
            values[variable] = value
        return values

    def interventional_effect(
        self,
        cause: str,
        effect: str,
        *,
        low: float = -1.0,
        high: float = 1.0,
        exogenous: Mapping[str, float] | None = None,
    ) -> float:
        if cause not in self._eq or effect not in self._eq:
            raise ValueError("cause/effect must be structural variables")
        if high == low:
            raise ValueError("intervention contrast must be non-zero")
        y_low = self.evaluate(exogenous=exogenous, interventions={cause: low})[effect]
        y_high = self.evaluate(exogenous=exogenous, interventions={cause: high})[effect]
        return (y_high - y_low) / (high - low)

    def effect_sign(self, cause: str, effect: str, *, eps: float = 1e-12) -> int:
        value = self.interventional_effect(cause, effect)
        if value > eps:
            return 1
        if value < -eps:
            return -1
        return 0

    def counterfactual(
        self,
        effect: str,
        *,
        intervention: Mapping[str, float],
        exogenous: Mapping[str, float] | None = None,
    ) -> float:
        if effect not in self._eq:
            raise ValueError("unknown counterfactual effect variable")
        # Holding U fixed while replacing one or more structural equations is
        # the deterministic SCM counterfactual for this evaluator.
        return self.evaluate(exogenous=exogenous, interventions=intervention)[effect]
