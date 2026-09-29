from dataclasses import dataclass
from .state import ComputeBudget
from .self_model import NexusSelfModel
@dataclass(frozen=True)
class MetaDecision:
    branch_depth:int;branch_fanout:int;expert_top_k:int;memory_limit:int;abstain:bool;reason:str
class MetaController:
    def decide(self,*,novelty,uncertainty,budget,self_model=None):
        n=max(0,min(1,float(novelty)));u=max(0,min(1,float(uncertainty)));hard=max(n,u)
        if budget.remaining_units<=.05:return MetaDecision(1,1,1,min(4,budget.max_memory_records),True,"compute_budget_exhausted")
        depth=min(budget.max_depth,1+int(hard>.35)+int(hard>.70));fanout=min(budget.max_fanout,2+int(hard>.50)+int(hard>.80));topk=min(budget.max_experts,2+int(hard>.55));mem=min(budget.max_memory_records,8+8*int(hard>.65));abstain=(u>.92 and n>.75)
        return MetaDecision(depth,fanout,topk,mem,abstain,"novelty_uncertainty_budget")
