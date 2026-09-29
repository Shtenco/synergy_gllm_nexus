from dataclasses import dataclass
from .state import ComputeBudget
from .self_model import NexusSelfModel

@dataclass(frozen=True)
class MetaDecision:
    branch_depth:int
    branch_fanout:int
    expert_top_k:int
    memory_limit:int
    abstain:bool
    reason:str
    verification_level:int=1
    weak_capabilities:tuple[str,...]=()

class MetaController:
    def decide(self,*,novelty,uncertainty,budget,self_model=None,capability_hints=()):
        n=max(0,min(1,float(novelty)));u=max(0,min(1,float(uncertainty)))
        weak=[]
        reliabilities=[]
        if self_model is not None:
            for cap in capability_hints:
                est=self_model.get(cap);r=float(est.reliability);reliabilities.append(r)
                if r<.55:weak.append(cap)
        capability_difficulty=(1-min(reliabilities)) if reliabilities else 0.0
        hard=max(n,u,capability_difficulty)

        if budget.remaining_units<=.05:
            return MetaDecision(1,1,1,min(4,budget.max_memory_records),True,'compute_budget_exhausted',3,tuple(sorted(weak)))

        depth=min(budget.max_depth,1+int(hard>.35)+int(hard>.70))
        fanout=min(budget.max_fanout,2+int(hard>.50)+int(hard>.80))
        topk=min(budget.max_experts,2+int(hard>.55))
        mem=min(budget.max_memory_records,8+8*int(hard>.65))

        verification=1+int(u>.55 or capability_difficulty>.45)+int(u>.80 or capability_difficulty>.65)
        verification=min(3,verification)
        abstain=(u>.92 and n>.75) or (capability_difficulty>.80 and u>.70)

        reason='novelty_uncertainty_budget'
        if weak:reason+='+self_model_weakness'
        return MetaDecision(depth,fanout,topk,mem,abstain,reason,verification,tuple(sorted(weak)))
