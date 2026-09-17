from nexus_gllm.unified_v3.contracts import ExecutionResult
from nexus_gllm.unified_v3.generalization import GeneralizationGovernor, InterventionCheck

def test_invariance_and_intervention():
    g=GeneralizationGovernor()
    base=ExecutionResult(truth=True)
    ok=g.audit(base,(ExecutionResult(truth=True),ExecutionResult(truth=True)),(InterventionCheck(ExecutionResult(truth=False),True),))
    assert ok.stable and ok.invariance_rate==1.0 and ok.intervention_sensitivity==1.0

def test_collapse_detector_fails_when_intervention_should_change_but_does_not():
    base=ExecutionResult(truth=True)
    a=GeneralizationGovernor().audit(base,(ExecutionResult(truth=True),),(InterventionCheck(ExecutionResult(truth=True),True),))
    assert not a.stable and a.violations
