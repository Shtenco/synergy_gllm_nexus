from __future__ import annotations
from pathlib import Path
import torch
from torch import nn
from .unified_ru_planner_v2 import features, PLAN_LABELS

class ResidualBlockV5(nn.Module):
    def __init__(self,h:int=1280):
        super().__init__()
        self.n1=nn.LayerNorm(h); self.l1=nn.Linear(h,h)
        self.n2=nn.LayerNorm(h); self.l2=nn.Linear(h,h)
        self.drop=nn.Dropout(.08)
    def forward(self,x):
        y=torch.nn.functional.gelu(self.l1(self.n1(x)))
        y=self.drop(y)
        y=torch.nn.functional.gelu(self.l2(self.n2(y)))
        return x+y

class UnifiedRUPlannerV5(nn.Module):
    def __init__(self,dim:int=4096,h:int=1280,blocks:int=4):
        super().__init__()
        self.inp=nn.Sequential(nn.Linear(dim,h),nn.GELU(),nn.LayerNorm(h))
        self.blocks=nn.Sequential(*[ResidualBlockV5(h) for _ in range(blocks)])
        self.head=nn.Sequential(nn.Linear(h,640),nn.GELU(),nn.LayerNorm(640),nn.Linear(640,len(PLAN_LABELS)))
    def forward(self,x): return self.head(self.blocks(self.inp(x)))
    @torch.no_grad()
    def predict(self,text:str):
        self.eval(); p=torch.softmax(self(features(text).unsqueeze(0))[0],0)
        i=int(p.argmax())
        return PLAN_LABELS[i],float(p[i]),{PLAN_LABELS[j]:float(p[j]) for j in range(len(PLAN_LABELS))}

def load_planner(path:str|Path):
    d=torch.load(Path(path),map_location="cpu")
    m=UnifiedRUPlannerV5();m.load_state_dict(d["state_dict"]);m.eval();return m
