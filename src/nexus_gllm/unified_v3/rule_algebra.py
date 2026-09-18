from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib
class RuleFamily(str,Enum): DIRECT='DIRECT'; SYMMETRIC='SYMMETRIC'; ASYMMETRIC='ASYMMETRIC'; TRANSITIVE='TRANSITIVE'; ANTI_TRANSITIVE='ANTI_TRANSITIVE'; INVERSE='INVERSE'; COMPOSITION='COMPOSITION'; CONDITIONAL='CONDITIONAL'; BLOCKED='BLOCKED'; TEMPORAL_REPLACEMENT='TEMPORAL_REPLACEMENT'
@dataclass(frozen=True)
class Variable: name:str
@dataclass(frozen=True)
class AtomPattern: operator_id:str; args:tuple[str,...]
@dataclass(frozen=True)
class RuleCondition: key:str; expected:str='1'
@dataclass(frozen=True)
class RuleBlocker: key:str
@dataclass(frozen=True)
class RuleClause:
    family:RuleFamily; operators:tuple[str,...]; conditions:tuple[RuleCondition,...]=(); blockers:tuple[RuleBlocker,...]=(); confidence:float=1.0
    @classmethod
    def transitive(cls,op): return cls(RuleFamily.TRANSITIVE,(op,))
    @classmethod
    def symmetric(cls,op): return cls(RuleFamily.SYMMETRIC,(op,))
    @classmethod
    def inverse(cls,a,b=None): return cls(RuleFamily.INVERSE,(a,b or a))
    @classmethod
    def composition(cls,a,b,c): return cls(RuleFamily.COMPOSITION,(a,b,c))
    @classmethod
    def conditional(cls,a,b,key='state'): return cls(RuleFamily.CONDITIONAL,(a,b),(RuleCondition(key),))
    @classmethod
    def blocked(cls,a,b=None,key='blocked'): return cls(RuleFamily.BLOCKED,(a,b or a),(),(RuleBlocker(key),))
def rule_shape_fingerprint(rule):
    shape=(rule.family.value,len(rule.operators),len(rule.conditions),len(rule.blockers))
    return hashlib.sha256(repr(shape).encode()).hexdigest()
