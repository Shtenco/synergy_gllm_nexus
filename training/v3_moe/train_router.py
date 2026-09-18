from __future__ import annotations
from pathlib import Path
import hashlib,json,torch
from .dataset import generate_dataset,FEATURES,EXPERTS
from .router_model import RouterTrainer
from .evaluate import evaluate_router
from .novelty_model import NoveltyTrainer,evaluate_novelty
from .calibration import ExpertCalibrator,evaluate_calibration
def logical_state_hash(model):
    h=hashlib.sha256()
    for k,v in sorted(model.state_dict().items()): h.update(k.encode()); h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()
def heuristic_recall(rows,k=3):
    mapping={'support':[0,1,5],'ru':[1,4,0],'evidence':[2,5,4],'context':[3,5,1],'graph':[4,5,1],'novelty':[5,0,2],'proof':[2,5,4]}; hit=tot=0
    for r in rows:
        signal=max(('support','ru','evidence','context','graph','novelty','proof'),key=lambda z:r.features[z]); sel=set(mapping[signal][:k]); u=set(r.useful); hit+=len(sel&u);tot+=len(u)
    return hit/max(tot,1)
def run_training(outdir,train_n=50000,dev_n=5000,oos_n=5000,seed=17,epochs=12):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True); tr=generate_dataset('A',train_n,seed); dv=generate_dataset('B',dev_n,seed+1); oo=generate_dataset('C',oos_n,seed+2)
    model=RouterTrainer(seed).fit(tr,dv,epochs=epochs); metrics=evaluate_router(model,oo,k=3); metrics['heuristic_topk_recall']=heuristic_recall(oo,3); metrics['dev_useful_expert_recall']=evaluate_router(model,dv,k=3)['useful_expert_recall']
    nov=NoveltyTrainer(seed).fit(tr,epochs=max(6,epochs//2)); novm=evaluate_novelty(nov,oo); metrics['novelty_accuracy']=novm['accuracy']; metrics['novelty_auroc']=novm['auroc']
    cal=ExpertCalibrator(seed).fit(model,dv,epochs=100); calm=evaluate_calibration(model,cal,oo); metrics['expert_calibration_ece']=calm['ece']; metrics['expert_calibration_brier']=calm['brier']
    x=torch.tensor([[r.features[k] for k in FEATURES] for r in oo],dtype=torch.float32)
    with torch.no_grad(): selected=model(x).topk(3,dim=1).indices.tolist()
    strict=sum(int(set(r.useful).issubset(set(sel)) and not (set(r.harmful)&set(sel))) for r,sel in zip(oo,selected))/max(len(oo),1); single=[sum(j in r.useful for r in oo)/max(len(oo),1) for j in range(len(EXPERTS))]; best=max(single) if single else 0.0
    metrics['strict_routing_success']=strict; metrics['best_single_expert_useful_rate']=best; metrics['moe_gain_over_best_single']=strict-best; metrics={k:round(float(v),6) for k,v in metrics.items()}
    ck=logical_state_hash(model); nk=logical_state_hash(nov); calk=logical_state_hash(cal); torch.save(model.state_dict(),out/'router.pt'); torch.save(nov.state_dict(),out/'novelty.pt'); torch.save(cal.state_dict(),out/'calibrator.pt')
    manifest={'train_n':train_n,'dev_n':dev_n,'oos_n':oos_n,'seed':seed,'epochs':epochs,'train_family':'A','dev_family':'B','oos_family':'C','features':list(FEATURES),'experts':list(EXPERTS)}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)); (out/'metrics.json').write_text(json.dumps(metrics,indent=2,sort_keys=True))
    return {'metrics':metrics,'checkpoint_sha256':ck,'novelty_sha256':nk,'calibrator_sha256':calk,'output_dir':str(out)}
