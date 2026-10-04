from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict


class CausalEvidenceKind(str, Enum):
    OBSERVATIONAL = "OBSERVATIONAL"
    INTERVENTIONAL = "INTERVENTIONAL"
    COUNTERFACTUAL = "COUNTERFACTUAL"


@dataclass(frozen=True)
class CausalEvidence:
    evidence_id: str
    cause: str
    effect: str
    kind: CausalEvidenceKind
    support: float
    trust: float = 1.0
    intervention_value: str | None = None
    outcome_value: str | None = None


@dataclass(frozen=True)
class CausalEdge:
    cause: str
    effect: str
    observational_mass: float
    interventional_mass: float
    counterfactual_mass: float
    contradiction_mass: float
    confidence: float
    identified: bool
    observational_signed: float = 0.0
    interventional_signed: float = 0.0
    counterfactual_signed: float = 0.0
    causal_agreement: float = 0.0
    effect_sign: int = 0


class CausalGraph:
    """Signed evidence-weighted causal graph.

    Correlation never identifies causality alone. Identification requires
    trusted interventional evidence plus agreeing counterfactual evidence.
    Observational disagreement can reduce confidence, but cannot erase a
    signed causal effect established by intervention and counterfactual.
    """

    def __init__(self, min_interventional_mass=.75, min_total_causal_mass=1.0):
        self.min_interventional_mass = float(min_interventional_mass)
        self.min_total_causal_mass = float(min_total_causal_mass)
        self._evidence: dict[tuple[str, str], list[CausalEvidence]] = defaultdict(list)

    def add(self, e: CausalEvidence):
        if e.cause == e.effect:
            raise ValueError("self-causal edge not allowed")
        if not -1 <= e.support <= 1:
            raise ValueError("support must be in [-1,1]")
        if not 0 <= e.trust <= 1:
            raise ValueError("trust must be in [0,1]")
        self._evidence[(e.cause, e.effect)].append(e)
        return self

    @staticmethod
    def _sign(value: float, *, eps: float = 1e-12) -> int:
        if value > eps:
            return 1
        if value < -eps:
            return -1
        return 0

    def edge(self, cause, effect) -> CausalEdge:
        rows = tuple(self._evidence.get((cause, effect), ()))
        signed = {
            CausalEvidenceKind.OBSERVATIONAL: 0.0,
            CausalEvidenceKind.INTERVENTIONAL: 0.0,
            CausalEvidenceKind.COUNTERFACTUAL: 0.0,
        }
        mass = {
            CausalEvidenceKind.OBSERVATIONAL: 0.0,
            CausalEvidenceKind.INTERVENTIONAL: 0.0,
            CausalEvidenceKind.COUNTERFACTUAL: 0.0,
        }
        for e in rows:
            weighted = float(e.support) * float(e.trust)
            signed[e.kind] += weighted
            mass[e.kind] += abs(weighted)

        obs_s = signed[CausalEvidenceKind.OBSERVATIONAL]
        inter_s = signed[CausalEvidenceKind.INTERVENTIONAL]
        cf_s = signed[CausalEvidenceKind.COUNTERFACTUAL]
        obs_m = mass[CausalEvidenceKind.OBSERVATIONAL]
        inter_m = mass[CausalEvidenceKind.INTERVENTIONAL]
        cf_m = mass[CausalEvidenceKind.COUNTERFACTUAL]

        inter_sign = self._sign(inter_s)
        cf_sign = self._sign(cf_s)
        same_causal_direction = inter_sign != 0 and inter_sign == cf_sign
        causal_mass = inter_m + cf_m
        causal_agreement = min(inter_m, cf_m) if same_causal_direction else 0.0

        identified = (
            inter_m >= self.min_interventional_mass
            and cf_m > 0.0
            and causal_mass >= self.min_total_causal_mass
            and same_causal_direction
        )
        effect_sign = inter_sign if identified else 0

        contradiction = 0.0
        if inter_sign and cf_sign and inter_sign != cf_sign:
            contradiction += min(inter_m, cf_m)
        obs_sign = self._sign(obs_s)
        if identified and obs_sign and obs_sign != effect_sign:
            contradiction += min(obs_m, causal_mass)

        total = obs_m + causal_mass
        if total <= 0:
            confidence = 0.0
        else:
            causal_support = causal_agreement + 0.5 * max(0.0, causal_mass - causal_agreement)
            confidence = max(0.0, min(1.0, causal_support / total))

        return CausalEdge(
            cause,
            effect,
            obs_m,
            inter_m,
            cf_m,
            contradiction,
            confidence,
            identified,
            observational_signed=obs_s,
            interventional_signed=inter_s,
            counterfactual_signed=cf_s,
            causal_agreement=causal_agreement,
            effect_sign=effect_sign,
        )

    def parents(self, effect, *, identified_only=True):
        out = []
        for cause, e in sorted(self._evidence):
            if e != effect:
                continue
            edge = self.edge(cause, effect)
            if not identified_only or edge.identified:
                out.append(edge)
        return tuple(out)

    def descendants(self, cause):
        seen = set()
        front = [cause]
        while front:
            x = front.pop(0)
            for (a, b) in self._evidence:
                if a != x:
                    continue
                if not self.edge(a, b).identified:
                    continue
                if b not in seen:
                    seen.add(b)
                    front.append(b)
        seen.discard(cause)
        return tuple(sorted(seen))

    def would_cycle(self, cause, effect):
        return cause == effect or cause in self.descendants(effect)


@dataclass(frozen=True)
class InterventionRecord:
    variable: str
    value: str
    observed_effects: tuple[tuple[str, str], ...]
    evidence_id: str


class InterventionLedger:
    def __init__(self):
        self._rows = []

    def record(self, variable, value, observed_effects, evidence_id):
        r = InterventionRecord(variable, value, tuple(observed_effects), evidence_id)
        self._rows.append(r)
        return r

    def rows(self):
        return tuple(self._rows)

    def to_evidence(self, effect_variable, positive_outcome):
        out = []
        for r in self._rows:
            for var, val in r.observed_effects:
                if var != effect_variable:
                    continue
                support = 1.0 if val == positive_outcome else -1.0
                out.append(
                    CausalEvidence(
                        r.evidence_id,
                        r.variable,
                        effect_variable,
                        CausalEvidenceKind.INTERVENTIONAL,
                        support,
                        1.0,
                        r.value,
                        val,
                    )
                )
        return tuple(out)
