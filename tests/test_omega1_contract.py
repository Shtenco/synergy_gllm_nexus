import json
from pathlib import Path

import torch

from nexus_gllm.schema import NodeType, GraphCard, TypedHyperEdge, AnswerGraph
from nexus_gllm.graph import DynamicHyperGraph
from nexus_gllm.graphscript import parse_graphscript, format_graphscript
from nexus_gllm.compiler_ru import RussianGraphCompiler
from nexus_gllm.rules import RuleEngine
from nexus_gllm.answer import AnswerResolver
from nexus_gllm.workspace import WorkspaceRetriever
from nexus_gllm.recurrent import GraphRecurrentCore, GraphTensorBatch
from nexus_gllm.realizer_ru import DeterministicRussianRealizer
from nexus_gllm.model import NexusGLLM


def test_graphscript_roundtrip_preserves_nodes_edges_and_answer():
    source = '''
NODE anton : PERSON ["Антон"]
NODE boris : PERSON ["Борис"]
EDGE anton -> boris : older_than CONF=1.0
QUERY oldest(?)
ANSWER anton
'''.strip()
    doc = parse_graphscript(source)
    rendered = format_graphscript(doc)
    reparsed = parse_graphscript(rendered)
    assert reparsed == doc


def test_dynamic_graph_rejects_duplicate_node_ids_and_tracks_version():
    graph = DynamicHyperGraph()
    graph.add_card(GraphCard(id="a", type=NodeType.PERSON, label="Антон"))
    assert graph.version == 1
    try:
        graph.add_card(GraphCard(id="a", type=NodeType.PERSON, label="Другой"))
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate IDs must be rejected")


def test_russian_compiler_and_rule_engine_infer_transitive_age():
    graph = DynamicHyperGraph()
    compiler = RussianGraphCompiler()
    compiler.compile_statement("Антон старше Бориса", graph)
    compiler.compile_statement("Борис старше Виктора", graph)
    RuleEngine().infer(graph)
    query = compiler.compile_question("Кто самый старший?", graph)
    answer = AnswerResolver().resolve(graph, query)
    assert answer.answer_value == "Антон"
    assert answer.confidence == 1.0


def test_workspace_is_bounded_and_keeps_seed():
    graph = DynamicHyperGraph()
    for i in range(20):
        graph.add_card(GraphCard(id=f"n{i}", type=NodeType.CONCEPT, label=f"N{i}", activation=float(i)))
    ws = WorkspaceRetriever().retrieve(graph, seeds=["n0"], limit=5)
    assert len(ws.node_ids) == 5
    assert "n0" in ws.node_ids


def test_recurrent_core_shapes_and_gradients():
    torch.manual_seed(7)
    core = GraphRecurrentCore(node_dim=16, edge_types=8, hidden_dim=24, op_count=6)
    batch = GraphTensorBatch(
        node_states=torch.randn(2, 4, 16, requires_grad=True),
        edge_index=torch.tensor([[[0, 1], [1, 2]], [[0, 2], [2, 3]]], dtype=torch.long),
        edge_types=torch.tensor([[1, 2], [2, 3]], dtype=torch.long),
        node_mask=torch.ones(2, 4, dtype=torch.bool),
    )
    out = core(batch, steps=3)
    assert out.node_states.shape == (2, 4, 24)
    assert out.operation_logits.shape == (2, 6)
    out.operation_logits.sum().backward()
    assert batch.node_states.grad is not None


def test_end_to_end_graph_native_russian_qa_and_persistence(tmp_path: Path):
    model = NexusGLLM()
    model.learn("Антон старше Бориса")
    model.learn("Борис старше Виктора")
    response = model.ask("Кто самый старший?")
    assert response.text == "Самый старший — Антон."
    assert response.answer_graph.answer_value == "Антон"

    path = tmp_path / "memory.json"
    model.save(path)
    loaded = NexusGLLM.load(path)
    assert loaded.ask("Кто самый старший?").text == "Самый старший — Антон."


def test_realizer_never_changes_answer_value():
    graph = DynamicHyperGraph()
    graph.add_card(GraphCard(id="moscow", type=NodeType.PLACE, label="Москва"))
    answer = AnswerGraph(answer_value="Москва", confidence=1.0, intent="identity")
    text = DeterministicRussianRealizer().realize(answer, graph)
    assert "Москва" in text
