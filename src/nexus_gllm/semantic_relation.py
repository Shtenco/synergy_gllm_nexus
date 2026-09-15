from __future__ import annotations
import torch
from torch import nn
import torch.nn.functional as F
from .operator_space import RELATIONS, operator_matrix, target_geometry

CONFUSION_PAIRS={(0,1):2.0,(4,5):2.0,(0,2):1.5,(1,2):1.25,(3,4):1.15}

class SemanticRelationCortex(nn.Module):
    def __init__(self,hash_buckets=4096,embed_dim=96,rule_dim=20,canon_dim=12,kappa=15000.0):
        super().__init__(); self.hash_buckets=hash_buckets; self.embed_dim=embed_dim; self.rule_dim=rule_dim
        self.ngram=nn.EmbeddingBag(hash_buckets,64,mode='mean')
        self.rule_enc=nn.Sequential(nn.Linear(rule_dim,32),nn.GELU(),nn.LayerNorm(32))
        self.surface=nn.Sequential(nn.Linear(96,embed_dim),nn.GELU(),nn.Linear(embed_dim,embed_dim),nn.LayerNorm(embed_dim))
        self.data_proto=nn.Parameter(torch.randn(6,embed_dim)*0.03)
        self.canon_proj=nn.Sequential(nn.Linear(canon_dim,embed_dim),nn.Tanh(),nn.Linear(embed_dim,embed_dim))
        self.rule_to_rel=nn.Linear(rule_dim,6,bias=False)
        self.residual=nn.Sequential(nn.Linear(embed_dim+rule_dim,64),nn.GELU(),nn.Linear(64,6))
        self.residual_gate=nn.Sequential(nn.Linear(embed_dim+rule_dim,32),nn.GELU(),nn.Linear(32,1),nn.Sigmoid())
        nn.init.constant_(self.residual_gate[2].bias,-2.0)
        self.critic=nn.GRU(input_size=4,hidden_size=24,batch_first=True)
        self.risk_head=nn.Linear(24,1); self.nota_head=nn.Linear(24,1)
        self.log_temp=nn.Parameter(torch.tensor(0.0))
        counts=torch.tensor([40000.,20000.,10000.,5000.,10000.,10000.])
        self.register_buffer('alpha',counts/(counts+kappa))
        self.register_buffer('canon_cards',operator_matrix())
        self.register_buffer('geometry_target',target_geometry())

    def prototypes(self):
        pd=F.normalize(self.data_proto,dim=-1)
        pc=F.normalize(self.canon_proj(self.canon_cards),dim=-1)
        p=F.normalize(self.alpha[:,None]*pd+(1-self.alpha[:,None])*pc,dim=-1)
        return pd,pc,p

    def forward(self,flat_ids,offsets,rules):
        ng=self.ngram(flat_ids,offsets)
        rr=self.rule_enc(rules)
        z=F.normalize(self.surface(torch.cat([ng,rr],-1)),dim=-1)
        pd,pc,p=self.prototypes()
        sim_data=z@pd.T; sim_canon=z@pc.T; sim=z@p.T
        rule_score=self.rule_to_rel(rules)
        temp=F.softplus(self.log_temp)+0.05
        raw_direct=rules[:,:6].clamp_min(0)
        direct=torch.log1p(raw_direct)
        prior=2.50*direct
        semantic=(sim/temp) + .08*rule_score
        top2=torch.topk(direct,2,dim=1).values
        evidence_margin=(top2[:,0]-top2[:,1]).clamp_min(0)
        semantic_scale=torch.exp(-1.5*evidence_margin).unsqueeze(1)
        resid=self.residual(torch.cat([z,rules],-1))
        gate=self.residual_gate(torch.cat([z,rules],-1))
        base=prior+semantic_scale*semantic
        learned_scores=base+semantic_scale*gate*resid
        raw_top2=torch.topk(raw_direct,2,dim=1).values
        strong_evidence=((raw_top2[:,0]>=0.75)&((raw_top2[:,0]-raw_top2[:,1])>=0.75)).unsqueeze(1)
        scores=torch.where(strong_evidence,prior,learned_scores)
        ev=torch.stack([sim_data,sim_canon,rule_score,base],dim=-1)
        _,h=self.critic(ev)
        h=h[-1]
        return {'z':z,'scores':scores,'base_scores':base,'sim_data':sim_data,'sim_canon':sim_canon,
                'rule_score':rule_score,'residual_gate':gate.squeeze(-1),'risk_logit':self.risk_head(h).squeeze(-1),
                'nota_logit':self.nota_head(h).squeeze(-1) + 2.4*(rules[:,6]+rules[:,7]).clamp(0,1),'prototypes':p}

    def geometry_loss(self):
        p=self.prototypes()[2]
        return F.mse_loss(p@p.T,self.geometry_target)

def hard_weight_matrix(labels:torch.Tensor)->torch.Tensor:
    n=labels.numel(); w=torch.ones(n,n,device=labels.device)
    for (a,b),v in CONFUSION_PAIRS.items():
        m=((labels[:,None]==a)&(labels[None,:]==b))|((labels[:,None]==b)&(labels[None,:]==a))
        w=torch.where(m,torch.full_like(w,float(v)),w)
    w.fill_diagonal_(0)
    return w

def hard_supcon_loss(z,labels,hard_weights=None,temperature=.12):
    n=z.shape[0]
    if n<2:return z.sum()*0
    sim=(z@z.T)/temperature
    eye=torch.eye(n,dtype=torch.bool,device=z.device)
    pos=(labels[:,None]==labels[None,:])&~eye
    neg=~(labels[:,None]==labels[None,:])&~eye
    weights=torch.ones_like(sim) if hard_weights is None else hard_weights.clamp_min(1e-3)
    exp=torch.exp(sim-sim.max(dim=1,keepdim=True).values)*~eye
    denom=(exp*torch.where(neg,weights,torch.ones_like(weights))).sum(1).clamp_min(1e-9)
    logp=sim-torch.log(denom)[:,None]-sim.max(dim=1,keepdim=True).values
    valid=pos.sum(1)>0
    if not valid.any():return z.sum()*0
    return (-(logp*pos).sum(1)[valid]/pos.sum(1)[valid].clamp_min(1)).mean()
