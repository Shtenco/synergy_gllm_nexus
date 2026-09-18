import torch
from torch import nn
from .rollout import EXPERTS
FEATURES=('support_count','text_len','cyrillic_ratio','option_count','digit_count','evidence_count','guillemet_count','has_arrow')
class Router(nn.Module):
    def __init__(self):super().__init__();self.net=nn.Sequential(nn.Linear(len(FEATURES),24),nn.Tanh(),nn.Linear(24,len(EXPERTS)))
    def forward(self,x):return self.net(x)
def _xy(rows):return torch.tensor([[r.case.router_features()[k] for k in FEATURES] for r in rows],dtype=torch.float32),torch.tensor([r.utilities() for r in rows],dtype=torch.float32)
def train_router(train,dev,seed=17,epochs=45):
    torch.manual_seed(seed);m=Router();x,y=_xy(train);opt=torch.optim.Adam(m.parameters(),lr=.04);loss=nn.SmoothL1Loss();g=torch.Generator().manual_seed(seed)
    for _ in range(epochs):
        order=torch.randperm(len(train),generator=g)
        for st in range(0,len(train),128):
            idx=order[st:st+128];z=loss(m(x[idx]),y[idx]);opt.zero_grad();z.backward();opt.step()
    m.eval();return m
def route_with_scores(model,rollouts,k=3):
    x,_=_xy(rollouts)
    with torch.no_grad():
        logits=model(x)
        return logits.topk(k,dim=1).indices.tolist(), logits.tolist()
def route(model,rollouts,k=3):
    return route_with_scores(model,rollouts,k)[0]
