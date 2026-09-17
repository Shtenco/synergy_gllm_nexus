from nexus_gllm.unified_v3.contracts import ExecutionResult, EpistemicState
from nexus_gllm.unified_v3.epistemic import EpistemicController
from nexus_gllm.unified_v3.renderer import RussianRenderer

def r(v): return ExecutionResult(truth=v)

def test_four_epistemic_states():
    c=EpistemicController()
    assert c.resolve((r(True),)).state is EpistemicState.PROVED
    assert c.resolve((r(False),)).state is EpistemicState.DISPROVED
    assert c.resolve((r(None),)).state is EpistemicState.UNRESOLVED
    assert c.resolve((r(True),r(False))).state is EpistemicState.CONFLICTED

def test_renderer_preserves_uncertainty():
    rr=RussianRenderer(); c=EpistemicController()
    assert 'Недостаточно данных' in rr.render(c.resolve((r(None),)))
    assert 'противореч' in rr.render(c.resolve((r(True),r(False)))).lower()
