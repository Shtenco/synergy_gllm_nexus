from __future__ import annotations
from dataclasses import dataclass
from itertools import product

from nexus_gllm.unified_v3.contracts import TaskProgram,WorldHypothesis
from .higher_order import HigherOrderContext,HigherOrderExecutor,HigherOrderStatus
from .program_ast import ProgramKind,ProgramNode


@dataclass(frozen=True)
class ProgramEvidenceCase:
    world:WorldHypothesis
    task:TaskProgram
    expected_truth:bool|None
    weight:float=1.0


@dataclass(frozen=True)
class ProgramCandidateScore:
    program:ProgramNode
    evidence_score:float
    complexity_cost:float
    unresolved_count:int
    contradictions:int
    total_score:float


@dataclass(frozen=True)
class ProgramSynthesisResult:
    candidates:tuple[ProgramCandidateScore,...]
    selected:ProgramNode|None
    evidence_cases:int


class ProgramSynthesisCortex:
    """Evidence-ranked compositional AST synthesis; no target-gold access."""
    def __init__(self,*,max_candidates=96,complexity_weight=.03,unresolved_penalty=.35,contradiction_penalty=1.0):
        self.max_candidates=int(max_candidates)
        self.complexity_weight=float(complexity_weight)
        self.unresolved_penalty=float(unresolved_penalty)
        self.contradiction_penalty=float(contradiction_penalty)
        self.executor=HigherOrderExecutor()

    @staticmethod
    def _operators(world,task):
        ops={f.operator.operator_id for f in world.facts}
        if task.operator_id:ops.add(task.operator_id)
        return tuple(sorted(ops))

    def generate(self,world:WorldHypothesis,task:TaskProgram):
        ops=self._operators(world,task)
        atoms=[]
        for op in ops:
            atoms.append(ProgramNode(ProgramKind.ATOM,f'rule:transitive:{op}'))
            atoms.append(ProgramNode(ProgramKind.ATOM,f'rule:symmetric:{op}'))
        # Cross-operator candidates are structural, not enumerated fixed families.
        for a,b in product(ops,repeat=2):
            if a!=b:
                atoms.append(ProgramNode(ProgramKind.ATOM,f'rule:inverse:{a}:{b}'))
        for a,b,c in product(ops,repeat=3):
            if len(atoms)>=self.max_candidates:break
            if len({a,b,c})>=2:
                atoms.append(ProgramNode(ProgramKind.ATOM,f'rule:composition:{a}:{b}:{c}'))
        # Add small compositional combinations without target labels.
        base=tuple(dict((x.program_id,x) for x in atoms).values())
        combos=[]
        for i,a in enumerate(base[:16]):
            for b in base[i+1:16]:
                combos.append(ProgramNode(ProgramKind.SEQUENCE,children=(a,b)))
                if len(base)+len(combos)>=self.max_candidates:break
            if len(base)+len(combos)>=self.max_candidates:break
        return tuple((base+tuple(combos))[:self.max_candidates])

    def score(self,program,evidence):
        fit=0.0;unresolved=0;contradictions=0
        for e in evidence:
            r=self.executor.execute(program,HigherOrderContext(e.world,e.task))
            pred=r.execution.truth if r.status is HigherOrderStatus.EXECUTED else None
            if pred is None:
                unresolved+=1
            elif pred==e.expected_truth:
                fit+=float(e.weight)
            else:
                contradictions+=1;fit-=self.contradiction_penalty*float(e.weight)
        complexity=float(program.complexity)
        total=fit-self.complexity_weight*complexity-self.unresolved_penalty*unresolved-self.contradiction_penalty*contradictions
        return ProgramCandidateScore(program,fit,complexity,unresolved,contradictions,total)

    def synthesize(self,world,task,evidence):
        evidence=tuple(evidence);programs=self.generate(world,task)
        scored=tuple(self.score(p,evidence) for p in programs)
        ranked=tuple(sorted(scored,key=lambda s:(-s.total_score,s.complexity_cost,s.program.program_id)))
        selected=ranked[0].program if ranked and evidence else None
        return ProgramSynthesisResult(ranked,selected,len(evidence))
