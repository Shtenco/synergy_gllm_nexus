from pathlib import Path

import torch

from nexus_gllm.model import NexusGLLM
from nexus_gllm.recurrent import GraphRecurrentCore


def test_nexus_loads_trained_core_checkpoint_and_reproduces_weights(tmp_path: Path):
    torch.manual_seed(123)
    core = GraphRecurrentCore(node_dim=32, edge_types=8, hidden_dim=64, op_count=6)
    checkpoint = tmp_path / "core.pt"
    torch.save({
        "state_dict": core.state_dict(),
        "config": {"node_dim": 32, "edge_types": 8, "hidden_dim": 64, "op_count": 6},
        "seed": 123,
        "epochs": 1,
        "format_version": 1,
    }, checkpoint)

    model = NexusGLLM(neural_seed=999)
    before = next(model.core.parameters()).detach().clone()
    info = model.load_core_checkpoint(checkpoint)
    after = next(model.core.parameters()).detach().clone()

    assert not torch.equal(before, after)
    assert torch.equal(after, next(core.parameters()).detach())
    assert info["format_version"] == 1
    assert info["config"]["hidden_dim"] == 64


def test_checkpoint_with_incompatible_dimensions_is_rejected(tmp_path: Path):
    bad = tmp_path / "bad.pt"
    torch.save({
        "state_dict": {},
        "config": {"node_dim": 16, "edge_types": 8, "hidden_dim": 64, "op_count": 6},
        "format_version": 1,
    }, bad)

    model = NexusGLLM()
    try:
        model.load_core_checkpoint(bad)
    except ValueError as exc:
        assert "node_dim" in str(exc)
    else:
        raise AssertionError("incompatible checkpoint must be rejected")
