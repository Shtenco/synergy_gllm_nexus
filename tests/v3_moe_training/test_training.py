from training.v3_moe.dataset import generate_dataset
from training.v3_moe.router_model import RouterTrainer
from training.v3_moe.evaluate import evaluate_router
def test_train_dev_oos_namespaces_and_no_split_feature():
    tr=generate_dataset('A',100,1); dv=generate_dataset('B',50,2); oo=generate_dataset('C',50,3)
    assert {x.episode_id for x in tr}.isdisjoint({x.episode_id for x in dv+oo})
    assert 'split' not in tr[0].features and 'gold' not in tr[0].features and 'track' not in tr[0].features
def test_learned_router_beats_random_topk_on_oos():
    tr=generate_dataset('A',3000,11); dv=generate_dataset('B',500,12); oo=generate_dataset('C',1000,13)
    m=RouterTrainer(seed=11).fit(tr,dv,epochs=8); ev=evaluate_router(m,oo,k=3)
    assert ev['useful_expert_recall']>ev['random_topk_recall']+0.15 and ev['negative_transfer_rate']<0.08
