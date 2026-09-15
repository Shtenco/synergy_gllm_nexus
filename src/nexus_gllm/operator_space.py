from __future__ import annotations
from dataclasses import dataclass
import torch

RELATIONS=("owned_by","located_in","is_a","older_than","before","causes")

@dataclass(frozen=True)
class OperatorCard:
    name:str; family:str; arity:int=2; directional:bool=True; functional:bool=False
    transitive:bool=False; symmetric:bool=False; temporal:bool=False; causal:bool=False
    taxonomic:bool=False; comparative:bool=False; state_relation:bool=False
    inverse_known:bool=False

CARDS={
 "owned_by":OperatorCard("owned_by","possession",functional=True,state_relation=True,inverse_known=True),
 "located_in":OperatorCard("located_in","location",functional=True,state_relation=True),
 "is_a":OperatorCard("is_a","taxonomy",taxonomic=True,transitive=True),
 "older_than":OperatorCard("older_than","comparison",transitive=True,comparative=True,inverse_known=True),
 "before":OperatorCard("before","temporal",transitive=True,temporal=True,inverse_known=True),
 "causes":OperatorCard("causes","causal",transitive=False,causal=True),
}
_FAMILIES=("possession","location","taxonomy","comparison","temporal","causal")

def card_vector(card:OperatorCard)->torch.Tensor:
    fam=[1.0 if card.family==f else 0.0 for f in _FAMILIES]
    flags=[float(card.functional),float(card.transitive),float(card.temporal),float(card.causal),float(card.taxonomic),float(card.comparative)]
    return torch.tensor(fam+flags,dtype=torch.float32)

def operator_matrix()->torch.Tensor:
    return torch.stack([card_vector(CARDS[r]) for r in RELATIONS],0)

def target_geometry()->torch.Tensor:
    x=operator_matrix()
    x=torch.nn.functional.normalize(x+1e-4,dim=-1)
    g=x@x.T
    g=0.55*g+0.45*torch.eye(len(RELATIONS))
    d=torch.sqrt(torch.diag(g).clamp_min(1e-9))
    g=g/(d[:,None]*d[None,:])
    return (g+g.T)/2
