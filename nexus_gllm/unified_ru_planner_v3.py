from __future__ import annotations
from pathlib import Path
import torch
from torch import nn
from .unified_ru_planner_v2 import features, PLAN_LABELS, ResidualBlock

class UnifiedRUPlannerV3Large(nn.Module):
    def __init__(self,dim:int=4096,h:int=1024,blocks:int=3):
        super().__init__()
        self.inp=nn.Sequential(nn.Linear(dim,h),nn.GELU(),nn.LayerNorm(h))
        self.blocks=nn.Sequential(*[ResidualBlock(h) for _ in range(blocks)])
        self.head=nn.Sequential(nn.Linear(h,512),nn.GELU(),nn.LayerNorm(512),nn.Dropout(.08),nn.Linear(512,len(PLAN_LABELS)))
    def forward(self,x): return self.head(self.blocks(self.inp(x)))
    @torch.no_grad()
    def predict(self,text:str):
        self.eval(); p=torch.softmax(self(features(text).unsqueeze(0))[0],0)
        i=int(p.argmax())
        return PLAN_LABELS[i],float(p[i]),{PLAN_LABELS[j]:float(p[j]) for j in range(len(PLAN_LABELS))}

def load_planner(path:str|Path):
    d=torch.load(Path(path),map_location="cpu")
    m=UnifiedRUPlannerV3Large()
    m.load_state_dict(d["state_dict"]);m.eval()
    return m
