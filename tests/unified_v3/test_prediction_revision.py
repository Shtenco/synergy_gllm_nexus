from nexus_gllm.unified_v3.contracts import *
from nexus_gllm.unified_v3.prediction import PredictionLedger
def test_prediction_confirmation_and_refutation_change_score():
    p=Prediction('p','h',('op:q','a','c'),True); led=PredictionLedger()
    yes=led.resolve((p,),(('op:q','a','c',True),))[0]; no=led.resolve((p,),(('op:q','a','c',False),))[0]
    assert yes.outcome is PredictionOutcome.CONFIRMED and yes.score_delta>0
    assert no.outcome is PredictionOutcome.REFUTED and no.score_delta<0
