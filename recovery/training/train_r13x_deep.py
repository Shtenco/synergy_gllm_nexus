from __future__ import annotations
import json, math, random, time
from pathlib import Path
import torch
from torch import nn
from nexus_gllm.r13x_trainable import TrainableR13XRouter, generate, tensors, save_checkpoint, LABELS

OUT=Path("artifacts/r13x_deeptrain"); OUT.mkdir(parents=True,exist_ok=True)
torch.manual_seed(20260926); random.seed(20260926)
train=generate(20260926,1800)
dev=generate(20260927,250)
blind=generate(20260928,250)
model=TrainableR13XRouter()
opt=torch.optim.AdamW(model.parameters(),lr=2e-3,weight_decay=1e-4)
loss_fn=nn.CrossEntropyLoss(label_smoothing=.03)
xtr,ytr=tensors(train); xdv,ydv=tensors(dev); xbl,ybl=tensors(blind)
bs=256; best=-1.0; best_state=None; history=[]; patience=12; stale=0
for epoch in range(1,121):
    model.train(); perm=torch.randperm(len(xtr)); total=0.0
    for i in range(0,len(xtr),bs):
        idx=perm[i:i+bs]; opt.zero_grad(set_to_none=True)
        loss=loss_fn(model(xtr[idx]),ytr[idx]); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step()
        total+=float(loss)*len(idx)
    model.eval()
    with torch.no_grad():
        dev_acc=float((model(xdv).argmax(1)==ydv).float().mean())
        blind_acc=float((model(xbl).argmax(1)==ybl).float().mean())
    history.append({"epoch":epoch,"train_loss":total/len(xtr),"dev_acc":dev_acc,"blind_monitor_only":blind_acc})
    if dev_acc>best+1e-6:
        best=dev_acc; stale=0; best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    else: stale+=1
    if stale>=patience and epoch>=30: break
model.load_state_dict(best_state)
model.eval()
with torch.no_grad():
    dev_acc=float((model(xdv).argmax(1)==ydv).float().mean())
    blind_acc=float((model(xbl).argmax(1)==ybl).float().mean())
meta={"seed":20260926,"train_examples":len(train),"dev_examples":len(dev),"blind_examples":len(blind),
      "epochs":len(history),"best_dev_acc":dev_acc,"blind_acc":blind_acc,"labels":LABELS,
      "note":"blind split never used for optimization/model selection"}
save_checkpoint(OUT/"r13x_router_deep.pt",model,meta)
(OUT/"training_metrics.json").write_text(json.dumps({"meta":meta,"history":history},indent=2),encoding="utf-8")
print(json.dumps(meta,indent=2))
