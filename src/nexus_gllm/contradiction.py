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

    def __init__(self, beliefs: BeliefGraph) -> None:
        self.beliefs = beliefs

    @staticmethod
    def _id(schema: str, keys: tuple[BeliefKey, ...]) -> str:
        canonical = "|".join([schema, *(
            f"{k.relation}:{k.subject}:{k.object}" for k in sorted(keys)
        )])
        return "ctr_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]

    def detect(self) -> tuple[ContradictionSet, ...]:
        snapshots = self.beliefs.snapshots()
        active_keys = [s.key for s in snapshots if s.posterior > 0.5]
        groups: dict[tuple[str, str], list[BeliefKey]] = {}
        for key in active_keys:
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
            for key in contradiction.belief_keys:
                current = self.beliefs.get(key)
                merged = tuple(sorted(set((*current.contradiction_set_ids, contradiction.id))))
                self.beliefs.set_contradictions(key, merged)

        return tuple(sorted(contradictions, key=lambda item: item.id))
