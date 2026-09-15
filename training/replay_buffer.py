from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import random


@dataclass(frozen=True)
class ReplayItem:
    id: str
    task: str
    payload: dict
    priority: float
    protected: bool
    generation: str

    @classmethod
    def create(cls, *, task: str, payload: dict, priority: float, protected: bool, generation: str) -> "ReplayItem":
        if priority <= 0:
            raise ValueError("priority must be positive")
        canonical = json.dumps({
            "task": task,
            "payload": payload,
            "priority": float(priority),
            "protected": bool(protected),
            "generation": generation,
        }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        rid = "rpl_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
        return cls(rid, task, dict(payload), float(priority), bool(protected), generation)


class ReplayBuffer:
    def __init__(self) -> None:
        self._items: dict[str, ReplayItem] = {}

    def add(self, item: ReplayItem) -> None:
        self._items[item.id] = item

    def __len__(self) -> int:
        return len(self._items)

    def sample(self, count: int, *, protected_quota: float = 0.25, seed: int = 17) -> tuple[ReplayItem, ...]:
        if count <= 0:
            return ()
        items = list(self._items.values())
        if not items:
            return ()
        rng = random.Random(seed)
        protected = [x for x in items if x.protected]
        ordinary = [x for x in items if not x.protected]
        protected_needed = min(len(protected), int((count * protected_quota) + 0.999999))

        def draw(pool: list[ReplayItem], n: int) -> list[ReplayItem]:
            pool = list(pool)
            rng.shuffle(pool)
            pool.sort(key=lambda x: (-x.priority, x.id))
            return pool[: min(n, len(pool))]

        chosen = draw(protected, protected_needed)
        remaining = count - len(chosen)
        chosen_ids = {x.id for x in chosen}
        rest_pool = [x for x in items if x.id not in chosen_ids]
        chosen.extend(draw(rest_pool, remaining))
        return tuple(chosen[:count])
