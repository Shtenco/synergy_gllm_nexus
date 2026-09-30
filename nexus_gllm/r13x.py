from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence
import ast, operator, re, time

@dataclass(frozen=True)
class Proposal:
    expert_id: str
    value: Any
    confidence: float
    uncertainty: float
    evidence: tuple[Any, ...] = ()
    provenance: tuple[str, ...] = ()
    verification: str | None = None
    verification_op: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

_AUTHORITY = {
    "EXACT_VERIFIED": 6, "DIRECT_EVIDENCE": 5, "CAUSAL_CONSISTENT": 4,
    "MEMORY_SUPPORTED": 3, "NEURAL_PROPOSAL": 2, "SURFACE_GUESS": 1,
}

class Blackboard:
    """Append-only hypothesis board. Resolution happens elsewhere."""
    def __init__(self): self.proposals: list[Proposal] = []
    def add(self, p: Proposal) -> None: self.proposals.append(p)
    def extend(self, ps: Iterable[Proposal]) -> None: self.proposals.extend(ps)
    def snapshot(self) -> tuple[Proposal, ...]: return tuple(self.proposals)

class R13XRouter:
    """Transparent deterministic router; learned routing can replace scoring later."""
    MANDATORY = ("semantic", "exact", "evidence")
    def route(self, features: Mapping[str, float], experts: Iterable[str], k: int | None = None) -> tuple[str, ...]:
        names=tuple(dict.fromkeys(experts))
        score={x:0.0 for x in names}
        for x in names:
            score[x] += float(features.get(x, 0.0))
            if x in self.MANDATORY: score[x] += 0.25
        ranked=sorted(names,key=lambda x:(-score[x],x))
        if k is None: k=min(len(ranked), max(3, int(features.get("top_k",4))))
        return tuple(ranked[:k])

class Verifier:
    """Small exact verifier layer. It never invents a semantic answer."""
    SAFE_BINOPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,
                 ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv,
                 ast.Mod:operator.mod,ast.Pow:operator.pow}
    def calculate(self, expr: str) -> Any:
        tree=ast.parse(expr,mode="eval")
        def ev(n):
            if isinstance(n,ast.Expression): return ev(n.body)
            if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return n.value
            if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
                v=ev(n.operand); return +v if isinstance(n.op,ast.UAdd) else -v
            if isinstance(n,ast.BinOp) and type(n.op) in self.SAFE_BINOPS:
                a,b=ev(n.left),ev(n.right); return self.SAFE_BINOPS[type(n.op)](a,b)
            raise ValueError("unsupported expression")
        return ev(tree)
    def verify(self,p: Proposal) -> Proposal:
        if p.verification_op=="CALCULATE" and isinstance(p.metadata.get("expression"),str):
            try:
                value=self.calculate(p.metadata["expression"])
                return Proposal(p.expert_id,value,p.confidence,p.uncertainty,p.evidence,p.provenance,
                                 "EXACT_VERIFIED","CALCULATE",p.metadata)
            except Exception:
                return p
        if p.verification_op=="EXACT_ASSERT" and "expected" in p.metadata:
            if p.value==p.metadata["expected"]:
                return Proposal(p.expert_id,p.value,p.confidence,p.uncertainty,p.evidence,p.provenance,
                                 "EXACT_VERIFIED",p.verification_op,p.metadata)
        return p

class R13XGovernor:
    def resolve(self, proposals: Sequence[Proposal]) -> Proposal | None:
        if not proposals: return None
        # Contradiction at equal authority is not silently voted away.
        groups={}
        for p in proposals:
            a=_AUTHORITY.get(p.verification or "SURFACE_GUESS",1)
            groups.setdefault(a,[]).append(p)
        for authority in sorted(groups,reverse=True):
            pool=groups[authority]
            vals=[]
            for p in pool:
                if not any(p.value==v for v in vals): vals.append(p.value)
            if len(vals)>1: return None
            if not vals: continue
            best=max(pool,key=lambda p:(p.confidence,-p.uncertainty,len(p.evidence),p.expert_id))
            if best.uncertainty>=.95 and authority<5: return None
            return best
        return None

class R13XEngine:
    """Evidence-first R1.3-X pipeline: route -> retain -> verify -> resolve/abstain."""
    def __init__(self, router: R13XRouter|None=None, verifier: Verifier|None=None, governor: R13XGovernor|None=None):
        self.router=router or R13XRouter(); self.verifier=verifier or Verifier(); self.governor=governor or R13XGovernor()
    def answer(self, query: str, proposals: Sequence[Proposal], *, features: Mapping[str,float]|None=None) -> Proposal|None:
        start=time.perf_counter()
        board=Blackboard()
        for p in proposals: board.add(self.verifier.verify(p))
        out=self.governor.resolve(board.snapshot())
        return out
    def resolve(self, proposals: Sequence[Proposal]) -> Proposal | None:
        return self.answer("",proposals)

class UnifiedR13X:
    def __init__(self, governor: R13XGovernor|None=None, router: R13XRouter|None=None):
        self.governor=governor or R13XGovernor(); self.router=router or R13XRouter()
        self.verifier=Verifier(); self.engine=R13XEngine(self.router,self.verifier,self.governor)
    def resolve(self, proposals: Sequence[Proposal]) -> Proposal|None:
        return self.engine.resolve(proposals)
