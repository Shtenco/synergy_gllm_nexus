from training.v3_hard_oos_d.generator import HardOOSDGenerator
from training.v3_hard_oos_d.adapter import compat_features
from training.v3_hard_oos_d import evaluate
import inspect

def test_adapter_is_exactly_eight_gold_free_features_and_evaluator_has_no_training():
    r=HardOOSDGenerator(407).generate(1)[0]
    f=compat_features(r,r.candidates[0])
    assert len(f)==8
    src=inspect.getsource(evaluate)
    assert '.fit(' not in src and 'optimizer' not in src.lower() and '.backward(' not in src
