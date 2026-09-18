from __future__ import annotations
from dataclasses import dataclass
from .contracts import RuleHypothesis,RuleProgram
from .rule_algebra import RuleClause
@dataclass(frozen=True)
class RuleDemonstration:
    operator_id: str; left: str; middle: str; right: str; consequence: bool
    @classmethod
    def chain(cls,operator,left,middle,right,consequence=True): return cls(operator,left,middle,right,consequence)
class RuleInducer:
    def candidates(self,demonstrations):
        if not demonstrations: return ()
        op=demonstrations[0].operator_id
        pos=sum(d.consequence for d in demonstrations); neg=len(demonstrations)-pos
        out=[]
        if pos: out.append(RuleClause.transitive(op))
        if len(demonstrations)<=1: out.append(RuleClause.symmetric(op))
        if neg: out.append(RuleClause.blocked(op))
        return tuple(out)
    def induce(self,demonstrations):
        if not demonstrations: return RuleProgram(())
        positives=sum(1 for d in demonstrations if d.consequence); negatives=len(demonstrations)-positives
        if positives and not negatives: return RuleProgram((RuleHypothesis('rule:transitive','transitive',1.0),), (RuleClause.transitive(demonstrations[0].operator_id),))
        if negatives and not positives: return RuleProgram((RuleHypothesis('rule:blocked','blocked_nontransitive',1.0),), (RuleClause.blocked(demonstrations[0].operator_id),))
        return RuleProgram(())
