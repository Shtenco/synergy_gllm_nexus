from nexus_gllm.unified_v3.cognitive.calibration import CalibrationLedger
from nexus_gllm.unified_v3.cognitive.meta_controller import MetaController
from nexus_gllm.unified_v3.cognitive.self_model import NexusSelfModel
from nexus_gllm.unified_v3.cognitive.state import ComputeBudget

def test_perfectly_calibrated_binary_stream_has_low_ece():
    c=CalibrationLedger()
    for _ in range(80):c.observe('x',.8,True)
    for _ in range(20):c.observe('x',.8,False)
    assert c.metrics('x').ece<.03

def test_overconfident_wrong_stream_has_high_brier_and_ece():
    c=CalibrationLedger()
    for _ in range(20):c.observe('x',.95,False)
    m=c.metrics('x');assert m.brier>.8 and m.ece>.9

def test_calibration_updates_self_model_error():
    c=CalibrationLedger()
    for _ in range(10):c.observe('x',.9,False)
    sm=NexusSelfModel();m=c.update_self_model(sm,'x')
    assert sm.get('x').calibration_error_ema>0 and m.n==10

def test_bad_calibration_increases_metacontrol_pressure():
    c=CalibrationLedger()
    for _ in range(20):c.observe('formal',.99,False)
    sm=NexusSelfModel()
    for _ in range(20):sm.observe('formal',success=True)
    b=ComputeBudget(1,3,4,4,16);mc=MetaController()
    base=mc.decide(novelty=.2,uncertainty=.6,budget=b,self_model=sm,capability_hints=('formal',))
    pressured=mc.decide(novelty=.2,uncertainty=.6,budget=b,self_model=sm,capability_hints=('formal',),calibration_ledger=c)
    assert pressured.verification_level>=base.verification_level
    assert 'calibration_pressure' in pressured.reason
