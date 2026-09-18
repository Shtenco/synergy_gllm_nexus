from training.v3_hard_oos_d.temporal import TemporalScenario
from training.v3_hard_oos_d.counterfactual import CounterfactualTrap

def test_temporal_current_vs_history_and_inhibitor():
    s=TemporalScenario.example()
    assert s.query(20)=='anna'
    assert s.query(50)=='boris'
    assert s.rule_enabled(35) is False

def test_counterfactual_necessary_redundant_and_irrelevant():
    t=CounterfactualTrap.example()
    assert t.apply('necessary') is False
    assert t.apply('redundant_a') is True
    assert t.apply('irrelevant') is True
    assert t.actual is True
