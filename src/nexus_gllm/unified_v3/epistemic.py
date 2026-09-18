from .contracts import EpistemicResult,EpistemicState
class EpistemicController:
    def __init__(self,consensus_threshold=0.7): self.consensus_threshold=consensus_threshold
    def resolve(self,results):
        vals={r.truth for r in results if r.truth is not None}
        if vals=={True,False}: state=EpistemicState.CONFLICTED
        elif vals=={True}: state=EpistemicState.PROVED
        elif vals=={False}: state=EpistemicState.DISPROVED
        else: state=EpistemicState.UNRESOLVED
        conf=1.0 if state in (EpistemicState.PROVED,EpistemicState.DISPROVED) else 0.0
        return EpistemicResult(state,(),conf)
    def resolve_weighted(self,weighted):
        total=sum(max(w,0) for _,w in weighted) or 1.0
        pos=sum(w for r,w in weighted if r.truth is True)/total; neg=sum(w for r,w in weighted if r.truth is False)/total; un=max(0.0,1-pos-neg)
        if pos>=self.consensus_threshold and neg<1-self.consensus_threshold: state=EpistemicState.PROVED
        elif neg>=self.consensus_threshold and pos<1-self.consensus_threshold: state=EpistemicState.DISPROVED
        else: state=EpistemicState.UNRESOLVED
        return EpistemicResult(state,(),max(pos,neg),pos,neg,un)
