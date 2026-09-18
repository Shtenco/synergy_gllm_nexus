import random,torch
from .dataset import FEATURES,EXPERTS
def evaluate_router(model,rows,k=3):
    x=torch.tensor([[r.features[z] for z in FEATURES] for r in rows],dtype=torch.float32)
    with torch.no_grad(): top=model(x).topk(k,dim=1).indices.tolist()
    hit=tot=harmful_selected=0; rr=random.Random(123); rhit=rtot=0
    for r,sel in zip(rows,top):
        u=set(r.useful); hs=set(r.harmful); ss=set(sel); hit+=len(u&ss); tot+=len(u); harmful_selected+=int(bool(hs&ss))
        rs=set(rr.sample(range(len(EXPERTS)),k)); rhit+=len(u&rs); rtot+=len(u)
    return {'useful_expert_recall':hit/max(tot,1),'random_topk_recall':rhit/max(rtot,1),'negative_transfer_rate':harmful_selected/max(len(rows),1)}
