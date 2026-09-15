from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .belief import BeliefGraph, BeliefKey


@dataclass(frozen=True)
class ContradictionSet:
    id: str
    schema: str
    belief_keys: tuple[BeliefKey, ...]


class ContradictionEngine:
    EXCLUSIVE_RELATIONS = frozenset({"owned_by", "located_in"})

    def __init__(self, beliefs: BeliefGraph, *, resolve_margin: float = 0.10) -> None:
        self.beliefs = beliefs
        self.resolve_margin = float(resolve_margin)

    @staticmethod
    def _id(schema: str, keys: tuple[BeliefKey, ...]) -> str:
        canonical = "|".join([schema, *(f"{k.relation}:{k.subject}:{k.object}" for k in sorted(keys))])
        return "ctr_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]

    def detect(self) -> tuple[ContradictionSet, ...]:
        snapshots = self.beliefs.snapshots()
        candidate_keys = [s.key for s in snapshots if s.posterior > 0.5 and s.support_evidence_ids]
        groups: dict[tuple[str, str], list[BeliefKey]] = {}
        for key in candidate_keys:
            if key.relation in self.EXCLUSIVE_RELATIONS:
                groups.setdefault((key.relation, key.subject), []).append(key)

        contradictions: list[ContradictionSet] = []
        for keys in groups.values():
            unique = sorted(set(keys))
            if len(unique) < 2:
                continue
            key_tuple = tuple(unique)
            contradictions.append(
                ContradictionSet(
                    id=self._id("functional_relation", key_tuple),
                    schema="functional_relation",
                    belief_keys=key_tuple,
                )
            )

        for contradiction in contradictions:
            ranked = sorted(
                (self.beliefs.get(key) for key in contradiction.belief_keys),
                key=lambda snapshot: (-snapshot.posterior, snapshot.key),
            )
            winner = ranked[0]
            runner_up = ranked[1]
            dominant = (
                winner.posterior >= self.beliefs.active_threshold
                and winner.posterior - runner_up.posterior >= self.resolve_margin
            )
            for snapshot in ranked:
                merged = tuple(sorted(set((*snapshot.contradiction_set_ids, contradiction.id))))
                if dominant and snapshot.key == winner.key:
                    status = "active"
                elif snapshot.posterior > 0.5:
                    status = "disputed"
                else:
                    status = snapshot.status
                self.beliefs.set_contradictions(snapshot.key, merged, status_override=status)

        return tuple(sorted(contradictions, key=lambda item: item.id))
