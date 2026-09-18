from __future__ import annotations
from pathlib import Path
import json,hashlib,torch,random
from .universe import SyntheticUniverseGenerator
from .ranker import HypothesisRanker
from .baselines import simplicity_accuracy,explained_accuracy
def _hash(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run_training(output_dir,*,train_episodes=10000,dev_episodes=1000,oos_episodes=1000,seed=17,epochs=10):
    random.seed(seed); torch.manual_seed(seed)
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    train=SyntheticUniverseGenerator('A',seed).generate(train_episodes); dev=SyntheticUniverseGenerator('B',seed+1).generate(dev_episodes); oos=SyntheticUniverseGenerator('C',seed+2).generate(oos_episodes)
    model=HypothesisRanker(8,seed=seed); initial=model.evaluate(dev); model.fit(train,epochs=epochs,lr=0.01)
    train_acc=model.evaluate(train); oos_acc=model.evaluate(oos)
    metrics={'train_accuracy':round(train_acc,6),'dev_accuracy':round(model.evaluate(dev),6),'oos_accuracy':round(oos_acc,6),'dev_initial_accuracy':round(initial,6),'oos_simplicity_baseline':round(simplicity_accuracy(oos),6),'oos_explained_baseline':round(explained_accuracy(oos),6),'generalization_gap':round(train_acc-oos_acc,6)}
    ck=out/'ranker.pt'; torch.save(model.model.state_dict(),ck)
    manifest={'train_episodes':train_episodes,'dev_episodes':dev_episodes,'oos_episodes':oos_episodes,'seed':seed,'epochs':epochs,'families':{'train':'A','dev':'B','oos':'C'}}
    (out/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2),encoding='utf-8'); (out/'metrics.json').write_text(json.dumps(metrics,sort_keys=True,indent=2),encoding='utf-8')
    return {'metrics':metrics,'checkpoint_sha256':_hash(ck),'manifest_sha256':_hash(out/'manifest.json'),'output_dir':str(out)}
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--output-dir',default='artifacts/v3_meta/run'); p.add_argument('--train-episodes',type=int,default=10000); p.add_argument('--dev-episodes',type=int,default=1000); p.add_argument('--oos-episodes',type=int,default=1000); p.add_argument('--seed',type=int,default=17); p.add_argument('--epochs',type=int,default=10); a=p.parse_args(); print(json.dumps(run_training(a.output_dir,train_episodes=a.train_episodes,dev_episodes=a.dev_episodes,oos_episodes=a.oos_episodes,seed=a.seed,epochs=a.epochs),indent=2))
