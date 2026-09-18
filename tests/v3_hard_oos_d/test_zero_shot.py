import pytest, json
from training.v3_hard_oos_d.evaluate import evaluate_zero_shot

def test_evaluator_rejects_unsealed_manifest(tmp_path):
    m=tmp_path/'manifest.json'; m.write_text(json.dumps({'sealed_before_evaluation':False}),encoding='utf-8')
    with pytest.raises(ValueError,match='not sealed'):
        evaluate_zero_shot(m,tmp_path/'missing.pt')
