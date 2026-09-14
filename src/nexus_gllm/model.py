from __future__ import annotations

from pathlib import Path

from .answer import AnswerResolver
from .compiler_ru import RussianGraphCompiler
from .graph import DynamicHyperGraph
from .persistence import save_graph_json, load_graph_json
from .realizer_ru import DeterministicRussianRealizer
from .rules import RuleEngine
from .schema import GLLMResponse
from .workspace import WorkspaceRetriever


class NexusGLLM:
    def __init__(self, graph: DynamicHyperGraph | None = None) -> None:
        self.graph = graph or DynamicHyperGraph()
        self.compiler = RussianGraphCompiler()
        self.rules = RuleEngine()
        self.resolver = AnswerResolver()
        self.realizer = DeterministicRussianRealizer()
        self.workspace = WorkspaceRetriever()

    def learn(self, text: str):
        update = self.compiler.compile_statement(text, self.graph)
        self.rules.infer(self.graph)
        return update

    def ask(self, text: str) -> GLLMResponse:
        query = self.compiler.compile_question(text, self.graph)
        self.rules.infer(self.graph)
        answer = self.resolver.resolve(self.graph, query)
        seed_ids = list(answer.support_node_ids)
        ws = self.workspace.retrieve(self.graph, seed_ids, limit=min(128, max(1, len(self.graph.cards))))
        rendered = self.realizer.realize(answer, self.graph)
        return GLLMResponse(
            text=rendered,
            answer_graph=answer,
            workspace_trace=ws.node_ids,
            confidence=answer.confidence,
        )

    def save(self, path: str | Path) -> None:
        save_graph_json(self.graph, path)

    @classmethod
    def load(cls, path: str | Path) -> "NexusGLLM":
        return cls(load_graph_json(path))
