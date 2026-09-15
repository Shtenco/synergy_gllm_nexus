from __future__ import annotations

from dataclasses import dataclass
from .graph import DynamicHyperGraph


@dataclass(frozen=True)
class ActiveWorkspace:
    node_ids: tuple[str, ...]
    graph_version: int


class WorkspaceRetriever:
    def retrieve(self, graph: DynamicHyperGraph, seeds: list[str] | tuple[str, ...], limit: int = 128) -> ActiveWorkspace:
        if limit <= 0:
            raise ValueError("limit must be positive")
        chosen: list[str] = []
        seen: set[str] = set()
        for node_id in seeds:
            if node_id in graph.cards and node_id not in seen:
                chosen.append(node_id)
                seen.add(node_id)
                if len(chosen) >= limit:
                    return ActiveWorkspace(tuple(chosen), graph.version)
        frontier = list(chosen)
        while frontier and len(chosen) < limit:
            current = frontier.pop(0)
            neighbors = sorted(graph.neighbors(current), key=lambda n: (-graph.cards[n].activation, n))
            for node_id in neighbors:
                if node_id in seen:
                    continue
                chosen.append(node_id)
                seen.add(node_id)
                frontier.append(node_id)
                if len(chosen) >= limit:
                    break
        if len(chosen) < limit:
            remaining = sorted(
                (n for n in graph.cards if n not in seen),
                key=lambda n: (-graph.cards[n].activation, -graph.cards[n].importance, n),
            )
            chosen.extend(remaining[: limit - len(chosen)])
        return ActiveWorkspace(tuple(chosen), graph.version)
