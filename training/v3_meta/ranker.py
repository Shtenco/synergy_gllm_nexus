from __future__ import annotations
import torch
from torch import nn
def feature_vector(ep,c):
    return [float(c.explained),float(c.contradictions),float(c.heldout),float(c.complexity),float(c.symmetry_signal),float(c.chain_signal),float(c.inverse_signal),float(c.blocker_signal)]
class Net(nn.Module):
    def __init__(self,d):
        super().__init__(); self.net=nn.Sequential(nn.Linear(d,16),nn.Tanh(),nn.Linear(16,1))
    def forward(self,x): return self.net(x).squeeze(-1)
class HypothesisRanker:
    def __init__(self,input_dim=8,seed=0):
        torch.manual_seed(seed); self.model=Net(input_dim)
    def _batch(self,rows):
        if not rows:return torch.empty((0,4,8)),torch.empty((0,),dtype=torch.long)
        x=torch.tensor([[feature_vector(ep,c) for c in ep.candidates] for ep in rows],dtype=torch.float32)
        y=torch.tensor([ep.gold_index for ep in rows],dtype=torch.long)
        return x,y
    def evaluate(self,rows):
        if not rows:return 0.0
        x,y=self._batch(rows); self.model.eval()
        with torch.no_grad():
            scores=self.model(x.reshape(-1,x.shape[-1])).reshape(x.shape[0],x.shape[1]); return float((scores.argmax(1)==y).float().mean())
    def fit(self,rows,epochs=8,lr=0.01,batch_size=512):
        x,y=self._batch(rows); opt=torch.optim.Adam(self.model.parameters(),lr=lr); lossfn=nn.CrossEntropyLoss(); self.model.train()
        for _ in range(epochs):
            for start in range(0,len(rows),batch_size):
                xb=x[start:start+batch_size]; yb=y[start:start+batch_size]
                scores=self.model(xb.reshape(-1,xb.shape[-1])).reshape(xb.shape[0],xb.shape[1]); loss=lossfn(scores,yb); opt.zero_grad(); loss.backward(); opt.step()
        return self
