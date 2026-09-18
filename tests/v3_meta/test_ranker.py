from training.v3_meta.ranker import feature_vector, HypothesisRanker
from training.v3_meta.universe import SyntheticUniverseGenerator
from training.v3_meta.baselines import explained_accuracy
def test_features_exclude_identity_and_smoke_ranker_learns():
    rows=SyntheticUniverseGenerator('A',11).generate(200); assert len(feature_vector(rows[0],rows[0].candidates[0]))==8
    m=HypothesisRanker(8); before=m.evaluate(rows); m.fit(rows,epochs=12,lr=0.02); after=m.evaluate(rows)
    assert after>=before and after>0.45
def test_oos_requires_combining_evidence_not_single_explained_shortcut():
    train=SyntheticUniverseGenerator('A',23).generate(2000); oos=SyntheticUniverseGenerator('C',29).generate(1000)
    base=explained_accuracy(oos); m=HypothesisRanker(8,seed=23); m.fit(train,epochs=10,lr=0.01); learned=m.evaluate(oos)
    assert base<0.75 and learned>base+0.08
