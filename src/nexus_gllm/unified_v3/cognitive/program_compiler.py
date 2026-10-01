from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .program_ast import ProgramKind,ProgramNode
from nexus_gllm.unified_v3.contracts import RuleProgram
from nexus_gllm.unified_v3.rule_algebra import RuleClause

class CompileStatus(str,Enum):
    COMPILED='COMPILED';MALFORMED='MALFORMED'

@dataclass(frozen=True)
class CompileResult:
    status:CompileStatus
    rule_program:RuleProgram=RuleProgram()
    errors:tuple[str,...]=()
    execution_mode:str='rule_program'

class CognitiveProgramCompiler:
    """Validate all CRC AST nodes and compile the primitive rule-program subset.

    Higher-order trees are validated here but interpreted by HigherOrderExecutor,
    because flattening IF/INHIBIT/TEMPORAL/COUNTERFACTUAL would destroy semantics.
    """
    def _atom_clause(self,node,errors):
        parts=node.symbol.split(':')
        if not parts or parts[0]!='rule':
            errors.append(f'malformed_atom:{node.symbol}');return None
        kind=parts[1].lower() if len(parts)>1 else ''
        try:
            if kind=='transitive' and len(parts)==3:return RuleClause.transitive(parts[2])
            if kind=='symmetric' and len(parts)==3:return RuleClause.symmetric(parts[2])
            if kind=='inverse' and len(parts)==4:return RuleClause.inverse(parts[2],parts[3])
            if kind=='composition' and len(parts)==5:return RuleClause.composition(parts[2],parts[3],parts[4])
        except Exception as exc:
            errors.append(f'compile_error:{type(exc).__name__}:{node.symbol}');return None
        errors.append(f'malformed_rule_atom:{node.symbol}');return None

    def compile(self,node):
        clauses=[];errors=[];higher=False
        def walk(n):
            nonlocal higher
            if n.kind is ProgramKind.ATOM:
                c=self._atom_clause(n,errors)
                if c is not None:clauses.append(c)
                return
            if n.kind in (ProgramKind.SEQUENCE,ProgramKind.COMPOSE):
                if not n.children:errors.append(f'empty_{n.kind.value.lower()}');return
                for c in n.children:walk(c)
                return
            if n.kind in (ProgramKind.IF,ProgramKind.INHIBIT):
                higher=True
                if len(n.children)!=2:errors.append(f'{n.kind.value.lower()}_arity')
                for c in n.children:walk(c)
                return
            if n.kind in (ProgramKind.TEMPORAL,ProgramKind.COUNTERFACTUAL):
                higher=True
                if len(n.children)!=1:errors.append(f'{n.kind.value.lower()}_arity')
                for c in n.children:walk(c)
                return
            errors.append(f'unknown_kind:{n.kind}')
        walk(node)
        if errors:return CompileResult(CompileStatus.MALFORMED,errors=tuple(errors),execution_mode='invalid')
        if higher:return CompileResult(CompileStatus.COMPILED,RuleProgram(),(),execution_mode='higher_order')
        return CompileResult(CompileStatus.COMPILED,RuleProgram(clauses=tuple(clauses)),(),execution_mode='rule_program')
