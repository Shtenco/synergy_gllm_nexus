from __future__ import annotations

import hashlib
import torch

from .graph import DynamicHyperGraph
from .workspace import ActiveWorkspace
from .recurrent import GraphTensorBatch


class GraphTensorizer:
    def __init__(self, node_dim: int = 32, edge_type_buckets: int = 8) -> None:
        self.node_dim = node_dim
        self.edge_type_buckets = edge_type_buckets

    def _node_vector(self, graph: DynamicHyperGraph, node_id: str) -> torch.Tensor:
        card = graph.cards[node_id]
        seed = f"{card.type.value}|{card.label}|{card.provenance}".encode("utf-8")
        digest = hashlib.sha256(seed).digest()
        values = [(digest[i % len(digest)] / 127.5) - 1.0 for i in range(self.node_dim)]
        if self.node_dim >= 4:
            values[0] = float(card.confidence) * 2.0 - 1.0
            values[1] = max(-1.0, min(1.0, float(card.activation)))
            values[2] = max(-1.0, min(1.0, float(card.importance)))
            values[3] = max(-1.0, min(1.0, float(card.consolidation_strength)))
        return torch.tensor(values, dtype=torch.float32)

    def _relation_bucket(self, relation: str) -> int:
        digest = hashlib.sha256(relation.encode("utf-8")).digest()
        return int(digest[0]) % self.edge_type_buckets

    def tensorize(self, graph: DynamicHyperGraph, workspace: ActiveWorkspace) -> GraphTensorBatch:
        node_ids = list(workspace.node_ids)
        if not node_ids:
            raise ValueError("workspace must contain at least one node")
        index = {node_id: i for i, node_id in enumerate(node_ids)}
        node_states = torch.stack([self._node_vector(graph, node_id) for node_id in node_ids], dim=0).unsqueeze(0)

        pairs: list[tuple[int, int]] = []
        edge_types: list[int] = []
        for edge in graph.find_edges():
            for src in edge.sources:
                for dst in edge.targets:
                    if src in index and dst in index:
                        pairs.append((index[src], index[dst]))
                        edge_types.append(self._relation_bucket(edge.relation))

        if pairs:
            edge_index = torch.tensor([pairs], dtype=torch.long)
            edge_type_tensor = torch.tensor([edge_types], dtype=torch.long)
        else:
            edge_index = torch.empty((1, 0, 2), dtype=torch.long)
            edge_type_tensor = torch.empty((1, 0), dtype=torch.long)

        node_mask = torch.ones((1, len(node_ids)), dtype=torch.bool)
        return GraphTensorBatch(
            node_states=node_states,
            edge_index=edge_index,
            edge_types=edge_type_tensor,
            node_mask=node_mask,
        )
