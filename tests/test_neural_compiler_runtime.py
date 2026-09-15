from pathlib import Path

import pytest

from nexus_gllm.compiler_neural import CompilerCharVocab, NeuralRussianGraphCompiler
from nexus_gllm.compiler_proposal import NeuralParseProposal
from nexus_gllm.model import NexusGLLM


def test_validated_neural_proposal_can_mutate_graph():
    model = NexusGLLM()
    text = "Антон старше Бориса"
    proposal = NeuralParseProposal(
        relation="older_than",
        subject_text="Антон",
        object_text="Бориса",
        subject_span=(0, 5),
        object_span=(13, 19),
        confidence=0.99,
        kind="statement",
    )
    result = model.learn_proposal(text, proposal)
    assert result["accepted"] is True
    assert any(e.relation == "older_than" and e.active for e in model.graph.edges.values())
    edge = next(e for e in model.graph.edges.values() if e.relation == "older_than")
    assert edge.provenance == "compiler:neural:validated"


def test_rejected_proposal_does_not_mutate_graph():
    model = NexusGLLM()
    proposal = NeuralParseProposal(
        relation="owned_by",
        subject_text="Автомобиль",
        object_text="Антон",
        subject_span=(0, 10),
        object_span=(22, 27),
        confidence=0.1,
        kind="statement",
    )
    before = model.graph.version
    result = model.learn_proposal("Автомобиль принадлежит Антону", proposal)
    assert result["accepted"] is False
    assert model.graph.version == before


def test_load_compiler_checkpoint_registers_vocabulary(tmp_path: Path):
    vocab = CompilerCharVocab.from_texts(["Антон старше Бориса"])
    relations = ("older_than", "abstain")
    compiler = NeuralRussianGraphCompiler(len(vocab), len(relations), emb_dim=8, hidden_dim=12)
    path = tmp_path / "compiler.pt"
    compiler.save_checkpoint(path, vocab, relations, seed=17, manifest_sha="sha")

    model = NexusGLLM()
    meta = model.load_compiler_checkpoint(path)
    assert meta["manifest_sha"] == "sha"
    assert model.compiler_relations == relations


def test_runtime_rejects_compiler_checkpoint_without_abstain(tmp_path: Path):
    vocab = CompilerCharVocab.from_texts(["Антон старше Бориса"])
    relations = ("older_than",)
    compiler = NeuralRussianGraphCompiler(len(vocab), len(relations), emb_dim=8, hidden_dim=12)
    path = tmp_path / "compiler.pt"
    compiler.save_checkpoint(path, vocab, relations, seed=17, manifest_sha="sha")

    with pytest.raises(ValueError, match="abstain"):
        NexusGLLM().load_compiler_checkpoint(path)
