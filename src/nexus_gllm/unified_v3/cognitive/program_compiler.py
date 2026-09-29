from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .program_ast import ProgramKind,ProgramNode
from nexus_gllm.unified_v3.contracts import RuleProgram
from nexus_gllm.unified_v3.rule_algebra import RuleClause
class CompileStatus(str,Enum): COMPILED='COMPILED';UNSUPPORTED='UNSUPPORTED';MALFORMED='MALFORMED'
@dataclass(frozen=True)
class CompileResult:
    status:CompileStatus;rule_program:RuleProgram=RuleProgram();unsupported:tuple[str,...]=();errors:tuple[str,...]=()
class CognitiveProgramCompiler:
    """Compile only CRC AST nodes with exact V3 executor semantics.

    Higher-order nodes fail closed until their typed semantics are implemented.
    """
    def compile(self,node):
        clauses=[];unsupported=[];errors=[]
        def walk(n):
            if n.kind is ProgramKind.ATOM:
                parts=n.symbol.split(':')
                if not parts or parts[0]!='rule':errors.append(f'malformed_atom:{n.symbol}');return
                kind=parts[1].lower() if len(parts)>1 else ''
                try:
                    if kind=='transitive' and len(parts)==3:clauses.append(RuleClause.transitive(parts[2]))
                    elif kind=='symmetric' and len(parts)==3:clauses.append(RuleClause.symmetric(parts[2]))
                    elif kind=='inverse' and len(parts)==4:clauses.append(RuleClause.inverse(parts[2],parts[3]))
                    elif kind=='composition' and len(parts)==5:clauses.append(RuleClause.composition(parts[2],parts[3],parts[4]))
                    else:errors.append(f'malformed_rule_atom:{n.symbol}')
                except Exception as exc:errors.append(f'compile_error:{type(exc).__name__}:{n.symbol}')
                return
            if n.kind in (ProgramKind.SEQUENCE,ProgramKind.COMPOSE):
                if not n.children:errors.append(f'empty_{n.kind.value.lower()}');return
                for c in n.children:walk(c)
                return
            unsupported.append(n.kind.value)
        walk(node)
        if errors:return CompileResult(CompileStatus.MALFORMED,errors=tuple(errors),unsupported=tuple(sorted(set(unsupported))))
        if unsupported:return CompileResult(CompileStatus.UNSUPPORTED,RuleProgram(clauses=tuple(clauses)),tuple(sorted(set(unsupported))))
        return CompileResult(CompileStatus.COMPILED,RuleProgram(clauses=tuple(clauses)))
