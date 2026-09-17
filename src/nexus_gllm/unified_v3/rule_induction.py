from __future__ import annotations
from dataclasses import dataclass
from .contracts import RuleHypothesis,RuleProgram

@dataclass(frozen=True)
class RuleDemonstration:
    operator_id: str
    left: str
    middle: str
    right: str
    consequence: bool
    @classmethod
    def chain(cls,operator,left,middle,right,consequence=True):
        return cls(operator,left,middle,right,consequence)

class RuleInducer:
    def induce(self,demonstrations:tuple[RuleDemonstration,...])->RuleProgram:
        if not demonstrations: return RuleProgram(())
        positives=sum(1 for d in demonstrations if d.consequence)
        negatives=len(demonstrations)-positives
        if positives and not negatives:
            return RuleProgram((RuleHypothesis('rule:transitive','transitive',1.0),))
        if negatives and not positives:
            return RuleProgram((RuleHypothesis('rule:blocked','blocked_nontransitive',1.0),))
        return RuleProgram(())
