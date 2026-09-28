from __future__ import annotations
import math, re, zlib
from pathlib import Path
import torch
from torch import nn

PLANS=("natural_lookup","multihop_compare","multihop_logic","causal_chain","memory_read","memory_arith","conflict_latest","world_transition","semantic_triple","formal_arith","formal_logic","evidence","mixed_memory_compare","abstain")
ROLES=("O","SUBJECT","OBJECT","VALUE","STATE","NUMBER","RELATION","TARGET")
TEMPORAL_ROLES=("NONE","HISTORIC","CURRENT")
BUCKET=16384
MAXLEN=112
HASHES=4
TOKEN_RE=re.compile(r"[A-Za-zА-Яа-яЁё0-9_]+|=>|->|[+*/=><()-]|[^\w\s]",re.UNICODE)

def _norm(s:str)->str:
    return s.casefold().replace("ё","е")

def token_hash_ids(token:str)->list[int]:
    t=_norm(token)
    forms=("w:"+t,"p:"+t[:4],"s:"+t[-4:],"g:"+t[:2]+"|"+t[-2:])
    return [1+(zlib.crc32(x.encode("utf-8"))%BUCKET) for x in forms]

class RussianCognitiveCortexV7Temporal(nn.Module):
    """Six-layer order-aware Russian cortex with four supervised heads."""
    def __init__(self,d_model:int=320,layers:int=6,heads:int=8,ff:int=1536):
        super().__init__()
        self.embedding=nn.Embedding(BUCKET+1,d_model,padding_idx=0)
        self.position=nn.Embedding(MAXLEN,d_model)
        layer=nn.TransformerEncoderLayer(
            d_model,heads,ff,dropout=.08,batch_first=True,
            norm_first=True,activation="gelu")
        self.encoder=nn.TransformerEncoder(layer,layers)
        self.norm=nn.LayerNorm(d_model)
        self.plan_head=nn.Sequential(
            nn.Linear(d_model,320),nn.GELU(),nn.LayerNorm(320),
            nn.Linear(320,len(PLANS)))
        self.relevance_head=nn.Linear(d_model,2)
        self.role_head=nn.Linear(d_model,len(ROLES))
        self.temporal_head=nn.Linear(d_model,len(TEMPORAL_ROLES))

    def forward(self,ids:torch.Tensor,padding_mask:torch.Tensor):
        x=self.embedding(ids).sum(2)/math.sqrt(HASHES)
        p=torch.arange(ids.shape[1],device=ids.device).unsqueeze(0)
        x=self.norm(self.encoder(x+self.position(p),src_key_padding_mask=padding_mask))
        return (
            self.plan_head(x[:,0]),
            self.relevance_head(x),
            self.role_head(x),
            self.temporal_head(x),
        )

def load_cortex(path:str|Path)->RussianCognitiveCortexV7Temporal:
    d=torch.load(Path(path),map_location="cpu")
    m=RussianCognitiveCortexV7Temporal()
    m.load_state_dict(d["state_dict"]);m.eval()
    return m
