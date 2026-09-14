from __future__ import annotations

from pathlib import Path
import torch

from .answer import AnswerResolver
from .compiler_ru import RussianGraphCompiler
from .graph import DynamicHyperGraph
from .persistence import save_graph_json, load_graph_json
from .realizer_ru import DeterministicRussianRealizer
from .recurrent import GraphRecurrentCore
from .rules import RuleEngine
from .schema import GLLMResponse
from .tensorizer import GraphTensorizer
from .workspace import WorkspaceRetriever


class NexusGLLM:
    CORE_CONFIG = {"node_dim": 32, "edge_types": 8, "hidden_dim": 64, "op_count": 6}

    def __init__(self, graph: DynamicHyperGraph | None = None, neural_seed: int = 17, cognition_steps: int = 3) -> None:
        self.graph = graph or DynamicHyperGraph()
        self.compiler = RussianGraphCompiler()
        self.rules = RuleEngine()
        self.resolver = AnswerResolver()
        self.realizer = DeterministicRussianRealizer()
        self.workspace = WorkspaceRetriever()
        self.tensorizer = GraphTensorizer(node_dim=self.CORE_CONFIG["node_dim"], edge_type_buckets=self.CORE_CONFIG["edge_types"])
        self.cognition_steps = cognition_steps
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(neural_seed)
            self.core = GraphRecurrentCore(**self.CORE_CONFIG)
        self.core.eval()
        self.core_checkpoint_info: dict | None = None

    def load_core_checkpoint(self, path: str | Path) -> dict:
        checkpoint = torch.load(Path(path), map_location="cpu", weights_only=False)
        config = checkpoint.get("config")
        if not isinstance(config, dict):
            raise ValueError("checkpoint config is missing")
        for key, expected in self.CORE_CONFIG.items():
            actual = config.get(key)
            if actual != expected:
                raise ValueError(f"incompatible checkpoint {key}: expected {expected}, got {actual}")
        state_dict = checkpoint.get("state_dict")
        if not isinstance(state_dict, dict):
            raise ValueError("checkpoint state_dict is missing")
        self.core.load_state_dict(state_dict, strict=True)
        self.core.eval()
        self.core_checkpoint_info = {
            "format_version": int(checkpoint.get("format_version", 1)),
            "config": dict(config),
            "seed": checkpoint.get("seed"),
            "epochs": checkpoint.get("epochs"),
        }
        return dict(self.core_checkpoint_info)

    def learn(self, text: str):
        update = self.compiler.compile_statement(text, self.graph)
        self.rules.infer(self.graph)
        return update

    def _cognize(self, workspace) -> tuple[float, ...]:
        batch = self.tensorizer.tensorize(self.graph, workspace)
        with torch.no_grad():
            out = self.core(batch, steps=self.cognition_steps)
        return tuple(round(float(v), 8) for v in out.operation_logits[0].cpu())

    def ask(self, text: str) -> GLLMResponse:
        query = self.compiler.compile_question(text, self.graph)
        self.rules.infer(self.graph)
        answer = self.resolver.resolve(self.graph, query)
        seed_ids = list(answer.support_node_ids)
        ws = self.workspace.retrieve(self.graph, seed_ids, limit=min(128, max(1, len(self.graph.cards))))
        cognition_logits = self._cognize(ws)
        rendered = self.realizer.realize(answer, self.graph)
        return GLLMResponse(
            text=rendered,
            answer_graph=answer,
            workspace_trace=ws.node_ids,
            confidence=answer.confidence,
            cognition_logits=cognition_logits,
            cognition_steps=self.cognition_steps,
        )

    def save(self, path: str | Path) -> None:
        save_graph_json(self.graph, path)

    @classmethod
    def load(cls, path: str | Path) -> "NexusGLLM":
        return cls(load_graph_json(path))
