from __future__ import annotations
import torch
from torch import nn
from .dataset import FEATURES,EXPERTS
class Net(nn.Module):
    def __init__(self):super().__init__(); self.m=nn.Sequential(nn.Linear(len(FEATURES),32),nn.Tanh(),nn.Linear(32,len(EXPERTS)))
    def forward(self,x):return self.m(x)
class RouterTrainer:
    def __init__(self,seed=0): self.seed=seed
    def _batch(self,rows):
        return torch.tensor([[r.features[k] for k in FEATURES] for r in rows],dtype=torch.float32),torch.tensor([r.utilities for r in rows],dtype=torch.float32)
    def fit(self,train,dev,epochs=40,batch_size=256):
        torch.manual_seed(self.seed); model=Net(); x,y=self._batch(train); opt=torch.optim.Adam(model.parameters(),lr=.03); lossfn=nn.SmoothL1Loss(); g=torch.Generator().manual_seed(self.seed)
        for _ in range(epochs):
            order=torch.randperm(len(train),generator=g)
            for start in range(0,len(train),batch_size):
                idx=order[start:start+batch_size]; loss=lossfn(model(x[idx]),y[idx]); opt.zero_grad(); loss.backward(); opt.step()
        model.eval(); return model
