from training.v3_meta.train import run_training
def test_seeded_training_is_reproducible(tmp_path):
    a=run_training(tmp_path/'a',train_episodes=300,dev_episodes=100,oos_episodes=100,seed=5,epochs=8)
    b=run_training(tmp_path/'b',train_episodes=300,dev_episodes=100,oos_episodes=100,seed=5,epochs=8)
    assert a['metrics']==b['metrics']
    assert a['metrics']['oos_accuracy']>=0.45
