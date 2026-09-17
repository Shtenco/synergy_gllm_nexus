from .contracts import EpistemicResult,EpistemicState
class EpistemicController:
    def resolve(self,results):
        vals={r.truth for r in results if r.truth is not None}
        if vals=={True,False}: state=EpistemicState.CONFLICTED
        elif vals=={True}: state=EpistemicState.PROVED
        elif vals=={False}: state=EpistemicState.DISPROVED
        else: state=EpistemicState.UNRESOLVED
        conf=1.0 if state in (EpistemicState.PROVED,EpistemicState.DISPROVED) else 0.0
        return EpistemicResult(state,(),conf)
