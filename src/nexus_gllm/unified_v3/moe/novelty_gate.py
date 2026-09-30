from dataclasses import dataclass
from enum import Enum
class NoveltyState(str,Enum): KNOWN='KNOWN'; UNCERTAIN='UNCERTAIN'; NOVEL='NOVEL'
@dataclass(frozen=True)
class NoveltySignals:
    max_confidence:float; router_entropy:float; semantic_distance:float; ast_novelty:float; disagreement:float; support_available:bool
@dataclass(frozen=True)
class NoveltyDecision:
    state:NoveltyState; required_experts:tuple[str,...]=()
class NoveltyGate:
    def classify(self,s):
        score=(1-s.max_confidence)+s.router_entropy+s.semantic_distance+s.ast_novelty+s.disagreement
        if score>=3.0:
            req=('v3',)+(('r7l',) if s.support_available else ())
            return NoveltyDecision(NoveltyState.NOVEL,req)
        if score>=1.8:return NoveltyDecision(NoveltyState.UNCERTAIN,('v3',))
        return NoveltyDecision(NoveltyState.KNOWN,())
