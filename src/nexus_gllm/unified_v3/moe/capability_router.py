from dataclasses import dataclass
from .contracts import CapabilityTag,RoutingDecision
@dataclass(frozen=True)
class RouterFeatures:
    support_count:int=0
    language:str=''
    evidence_conflict:bool=False
    context_depth:int=0
    graph_signal:float=0.0
    proof_signal:float=0.0
    novelty:float=0.0
    cost_signal:float=0.0
    ru_signal:float|None=None
    evidence_signal:float|None=None
class HeuristicCapabilityRouter:
    def route(self,f,registry,k_min=2,k_max=4):
        score={s.expert_id:0.05 for s in registry.active()}
        for s in registry.active():
            tags=set(s.capability_tags)
            if f.support_count and CapabilityTag.FAST_INDUCTION in tags: score[s.expert_id]+=2.0
            if f.language=='ru' and CapabilityTag.LANGUAGE in tags: score[s.expert_id]+=1.5
            if f.evidence_conflict and CapabilityTag.EVIDENCE in tags: score[s.expert_id]+=2.0
            if f.context_depth and CapabilityTag.CONTEXT in tags: score[s.expert_id]+=1.5
            if f.graph_signal>0 and CapabilityTag.GRAPH in tags: score[s.expert_id]+=f.graph_signal
            if CapabilityTag.HYPOTHESIS in tags: score[s.expert_id]+=.4
        ranked=sorted(score.items(),key=lambda x:(-x[1],x[0]))
        k=max(k_min,min(k_max,k_min + int(f.novelty>.7)))
        return RoutingDecision(tuple(x[0] for x in ranked[:k]),tuple(ranked))
