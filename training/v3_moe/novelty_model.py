import torch
from torch import nn
from .dataset import FEATURES
class NoveltyNet(nn.Module):
    def __init__(self): super().__init__(); self.m=nn.Sequential(nn.Linear(len(FEATURES),12),nn.ReLU(),nn.Linear(12,1))
    def forward(self,x): return self.m(x).squeeze(-1)
class NoveltyTrainer:
    def __init__(self,seed=0): self.seed=seed
    def fit(self,rows,epochs=6,batch_size=256):
        torch.manual_seed(self.seed); m=NoveltyNet(); x=torch.tensor([[r.features[k] for k in FEATURES] for r in rows],dtype=torch.float32); y=torch.tensor([1.0 if r.features['novelty']>.7 else 0.0 for r in rows]); g=torch.Generator().manual_seed(self.seed)
        opt=torch.optim.Adam(m.parameters(),lr=.08); lossfn=nn.BCEWithLogitsLoss()
        for _ in range(epochs):
            order=torch.randperm(len(rows),generator=g)
            for start in range(0,len(rows),batch_size):
                idx=order[start:start+batch_size]; loss=lossfn(m(x[idx]),y[idx]); opt.zero_grad(); loss.backward(); opt.step()
        m.eval(); return m
def _auroc(scores,labels):
    pairs=sorted(zip([float(x) for x in scores],[int(x) for x in labels]),key=lambda z:z[0]); pos=sum(y for _,y in pairs); neg=len(pairs)-pos
    if not pos or not neg:return 1.0
    rank_sum=0.0; i=0
    while i<len(pairs):
        j=i+1
        while j<len(pairs) and pairs[j][0]==pairs[i][0]: j+=1
        avg=(i+1+j)/2.0; rank_sum += avg*sum(y for _,y in pairs[i:j]); i=j
    return (rank_sum-pos*(pos+1)/2)/(pos*neg)
def evaluate_novelty(model,rows):
    if not rows:return {'accuracy':0.0,'auroc':0.0}
    x=torch.tensor([[r.features[k] for k in FEATURES] for r in rows],dtype=torch.float32); y=torch.tensor([1 if r.features['novelty']>.7 else 0 for r in rows])
    with torch.no_grad(): scores=torch.sigmoid(model(x)); p=(scores>=.5).long()
    return {'accuracy':float((p==y).float().mean()),'auroc':float(_auroc(scores.tolist(),y.tolist()))}
