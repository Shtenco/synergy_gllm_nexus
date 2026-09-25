from collections import defaultdict
from .contracts import FusedProposalSet
from .lineage import lineage_independence_weight
class ProposalFusion:
    def fuse(self,proposals,registry):
        specs=[registry.get(p.expert_id) for p in proposals]
        lw=lineage_independence_weight(specs)
        scores=defaultdict(float); prov=defaultdict(list); facts=[]
        for p in proposals:
            bonus=.15 if p.evidence_items else 0.0
            base=max(0.0,min(1.0,p.confidence))+bonus
            for a in p.answer_candidates:
                scores[a]+=base*lw[p.expert_id]; prov[a].append(p.expert_id)
            facts.extend(p.semantic_facts)
        ranked=sorted(scores.items(),key=lambda x:(-x[1],str(x[0])))
        lead=ranked[0][0] if ranked else None
        return FusedProposalSet(lead,tuple(facts),tuple(ranked),(),tuple(prov.get(lead,())))
