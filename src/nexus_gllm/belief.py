from __future__ import annotations

from dataclasses import dataclass
import math

from .evidence import EvidenceLedger, EvidenceRecord
from .source_reliability import SourceRegistry


def _clamp_probability(value: float, eps: float = 1e-6) -> float:
    return min(1.0 - eps, max(eps, float(value)))


def _logit(probability: float) -> float:
    p = _clamp_probability(probability)
    return math.log(p / (1.0 - p))


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


@dataclass(frozen=True, order=True)
class BeliefKey:
    relation: str
    subject: str
    object: str

    def as_tuple(self) -> tuple[str, str, str]:
        return (self.relation, self.subject, self.object)


@dataclass(frozen=True)
class BeliefSnapshot:
    key: BeliefKey
    posterior: float
    log_odds: float
    status: str
    support_evidence_ids: tuple[str, ...] = ()
    attack_evidence_ids: tuple[str, ...] = ()
    contradiction_set_ids: tuple[str, ...] = ()
    last_revision: int = 0


@dataclass(frozen=True)
class BeliefUpdate:
    snapshot: BeliefSnapshot
    evidence_id: str
    gradient_steps: int = 0


class BeliefGraph:
    def __init__(
        self,
        ledger: EvidenceLedger,
        sources: SourceRegistry,
        *,
        prior: float = 0.5,
        active_threshold: float = 0.75,
        retracted_threshold: float = 0.25,
    ) -> None:
        self.ledger = ledger
        self.sources = sources
        self.prior = _clamp_probability(prior)
        self.active_threshold = float(active_threshold)
        self.retracted_threshold = float(retracted_threshold)
        self._revision = 0
        self._snapshots: dict[BeliefKey, BeliefSnapshot] = {}

    @staticmethod
    def _evidence_strength(record: EvidenceRecord) -> float:
        combined = _clamp_probability(record.source_reliability * record.confidence)
        return _logit(combined)

    def _compute(self, key: BeliefKey) -> BeliefSnapshot:
        records = self.ledger.for_proposition(key.as_tuple())
        support = tuple(r.id for r in records if r.polarity == "support")
        attack = tuple(r.id for r in records if r.polarity == "attack")
        log_odds = _logit(self.prior)
        for record in records:
            strength = self._evidence_strength(record)
            log_odds += strength if record.polarity == "support" else -strength
        posterior = _sigmoid(log_odds)
        if support and attack:
            status = "disputed"
        elif posterior >= self.active_threshold:
            status = "active"
        elif posterior <= self.retracted_threshold:
            status = "retracted"
        else:
            status = "unknown"
        return BeliefSnapshot(
            key=key,
            posterior=posterior,
            log_odds=log_odds,
            status=status,
            support_evidence_ids=support,
            attack_evidence_ids=attack,
            contradiction_set_ids=self._snapshots.get(key, BeliefSnapshot(key, self.prior, _logit(self.prior), "unknown")).contradiction_set_ids,
            last_revision=self._revision,
        )

    def observe(self, record: EvidenceRecord) -> BeliefUpdate:
        key = BeliefKey(*record.proposition_key)
        self.ledger.add(record)
        self._revision += 1
        snapshot = self._compute(key)
        self._snapshots[key] = snapshot
        return BeliefUpdate(snapshot=snapshot, evidence_id=record.id, gradient_steps=0)

    def get(self, key: BeliefKey) -> BeliefSnapshot:
        existing = self._snapshots.get(key)
        if existing is not None:
            return existing
        return BeliefSnapshot(
            key=key,
            posterior=self.prior,
            log_odds=_logit(self.prior),
            status="unknown",
            last_revision=self._revision,
        )

    def snapshots(self) -> tuple[BeliefSnapshot, ...]:
        return tuple(self._snapshots[key] for key in sorted(self._snapshots))

    def set_contradictions(self, key: BeliefKey, contradiction_ids: tuple[str, ...]) -> BeliefSnapshot:
        current = self.get(key)
        updated = BeliefSnapshot(
            key=current.key,
            posterior=current.posterior,
            log_odds=current.log_odds,
            status="disputed" if contradiction_ids and current.status == "active" else current.status,
            support_evidence_ids=current.support_evidence_ids,
            attack_evidence_ids=current.attack_evidence_ids,
            contradiction_set_ids=tuple(sorted(set(contradiction_ids))),
            last_revision=current.last_revision,
        )
        self._snapshots[key] = updated
        return updated
