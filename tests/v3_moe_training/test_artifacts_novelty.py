from training.v3_moe.train_router import run_training
from training.v3_moe.novelty_model import NoveltyTrainer,evaluate_novelty
from training.v3_moe.dataset import generate_dataset
def test_training_persists_reproducible_metrics(tmp_path):
    a=run_training(tmp_path/'a',train_n=1000,dev_n=200,oos_n=300,seed=17,epochs=6); b=run_training(tmp_path/'b',train_n=1000,dev_n=200,oos_n=300,seed=17,epochs=6)
    assert a['metrics']==b['metrics'] and a['checkpoint_sha256']==b['checkpoint_sha256']
def test_novelty_detector_separates_novel_oos():
    tr=generate_dataset('A',1500,21); oo=generate_dataset('C',500,22)
    assert evaluate_novelty(NoveltyTrainer(seed=21).fit(tr,epochs=6),oo)['accuracy']>0.8
def test_training_report_contains_federation_metrics(tmp_path):
    m=run_training(tmp_path/'m',train_n=1200,dev_n=300,oos_n=400,seed=23,epochs=8)['metrics']
    for key in ('expert_calibration_ece','expert_calibration_brier','novelty_auroc','strict_routing_success','best_single_expert_useful_rate','moe_gain_over_best_single'): assert key in m
