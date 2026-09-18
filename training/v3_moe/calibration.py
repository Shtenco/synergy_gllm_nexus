from __future__ import annotations
import torch
from torch import nn
from .dataset import FEATURES,EXPERTS
class Calibrator(nn.Module):
    def __init__(self,n): super().__init__(); self.scale=nn.Parameter(torch.ones(n)); self.bias=nn.Parameter(torch.zeros(n))
    def forward(self,scores): return scores*self.scale + self.bias
class ExpertCalibrator:
    def __init__(self,seed=0): self.seed=seed
    def fit(self,router,rows,epochs=80):
        torch.manual_seed(self.seed); x=torch.tensor([[r.features[k] for k in FEATURES] for r in rows],dtype=torch.float32); y=torch.zeros((len(rows),len(EXPERTS)),dtype=torch.float32)
        for i,r in enumerate(rows):
            for j in r.useful:y[i,j]=1.0
        with torch.no_grad(): scores=router(x)
        cal=Calibrator(len(EXPERTS)); opt=torch.optim.Adam(cal.parameters(),lr=.05); lossfn=nn.BCEWithLogitsLoss()
        for _ in range(epochs):
            loss=lossfn(cal(scores),y); opt.zero_grad(); loss.backward(); opt.step()
        cal.eval(); return cal
def _ece(probs,targets,bins=10):
    p=probs.flatten(); y=targets.flatten(); e=0.0
    for b in range(bins):
        lo=b/bins; hi=(b+1)/bins; mask=(p>=lo)&((p<hi) if b<bins-1 else (p<=hi))
        if mask.any(): e += float(mask.float().mean())*abs(float(p[mask].mean())-float(y[mask].mean()))
    return e
def evaluate_calibration(router,calibrator,rows):
    x=torch.tensor([[r.features[k] for k in FEATURES] for r in rows],dtype=torch.float32); y=torch.zeros((len(rows),len(EXPERTS)),dtype=torch.float32)
    for i,r in enumerate(rows):
        for j in r.useful:y[i,j]=1.0
    with torch.no_grad(): probs=torch.sigmoid(calibrator(router(x)))
    return {'ece':_ece(probs,y),'brier':float(((probs-y)**2).mean())}
