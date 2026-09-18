from training.v3_moe.dataset import generate_dataset
from training.v3_moe.train_router import heuristic_recall
from training.v3_moe.router_model import RouterTrainer
from training.v3_moe.evaluate import evaluate_router
def test_curriculum_is_not_solved_by_single_signal_heuristic():
    assert heuristic_recall(generate_dataset('C',2000,31),3)<0.90
def test_learned_router_combines_signals_on_oos():
    tr=generate_dataset('A',10000,29); dv=generate_dataset('B',1500,30); oo=generate_dataset('C',2000,31)
    m=evaluate_router(RouterTrainer(29).fit(tr,dv,epochs=40),oo,k=3)
    assert m['useful_expert_recall']>=0.95 and m['negative_transfer_rate']<=0.02
