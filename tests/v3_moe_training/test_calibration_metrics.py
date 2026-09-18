from training.v3_moe.dataset import generate_dataset
from training.v3_moe.router_model import RouterTrainer
from training.v3_moe.calibration import ExpertCalibrator,evaluate_calibration
from training.v3_moe.novelty_model import NoveltyTrainer,evaluate_novelty
def test_posthoc_expert_calibration_reaches_low_ece_on_oos():
    tr=generate_dataset('A',8000,41); dv=generate_dataset('B',2000,42); oo=generate_dataset('C',2500,43)
    router=RouterTrainer(41).fit(tr,dv,epochs=10); cal=ExpertCalibrator(seed=41).fit(router,dv,epochs=80)
    assert evaluate_calibration(router,cal,oo)['ece']<0.10
def test_novelty_reports_high_auroc_on_oos():
    tr=generate_dataset('A',5000,51); oo=generate_dataset('C',2000,52)
    assert evaluate_novelty(NoveltyTrainer(seed=51).fit(tr,epochs=8),oo)['auroc']>=0.90
