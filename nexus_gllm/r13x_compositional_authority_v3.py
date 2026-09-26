from __future__ import annotations

import ast
import re
from dataclasses import dataclass, asdict
from typing import Any

from .r13x_exact_organs_v2 import ExactOrganV2


@dataclass
class AuthorityDecision:
    status: str
    answer: Any = None
    authority: str = "ABSTAIN"
    proof_scope: str = "NONE"
    semantic_atom_id: str | None = None
    semantic_governor_correct: bool | None = None
    conflict: bool = False
    trace: tuple[str, ...] = ()

    def to_dict(self):
        return asdict(self)


class CompositionalAuthorityGovernorV3:
    """Resolve conflicts between frozen learned knowledge and verified executable proof.

    Rules:
    1. A frozen semantic atom marked governor_correct=False is never final authority.
    2. VERIFIED proof wins only when it covers the whole requested expression.
    3. A VERIFIED sub-proof may be used as an intermediate result only if the
       remaining outer composition is explicitly supported and independently executed.
    4. Unsupported composition fails closed.
    """

    SAFE_CALLS = {"range", "list", "len", "sum", "min", "max", "abs"}
    SAFE_BINOPS = {
        ast.Add: lambda a,b:a+b,
        ast.Sub: lambda a,b:a-b,
        ast.Mult: lambda a,b:a*b,
        ast.Div: lambda a,b:a/b,
        ast.FloorDiv: lambda a,b:a//b,
        ast.Mod: lambda a,b:a%b,
        ast.Pow: lambda a,b:a**b,
    }
    SAFE_UNARY = {ast.UAdd: lambda a:+a, ast.USub: lambda a:-a}

    def __init__(self, exact: ExactOrganV2):
        self.exact=exact

    @staticmethod
    def _norm(s:str)->str:
        return re.sub(r"\s+"," ",str(s or "").strip().casefold().replace("ё","е"))

    @staticmethod
    def _extract_python_expression(question:str)->str|None:
        q=str(question or "").strip()
        # Prefer expression after "равно"; fall back to text after Python marker.
        m=re.search(r"(?:чему\s+равно|равно)\s+(.+?)(?:\?|$)",q,re.I)
        expr=m.group(1).strip() if m else None
        if expr is None and "python" in q.casefold():
            m=re.search(r"python[^:]*[:—-]?\s*(.+?)(?:\?|$)",q,re.I)
            expr=m.group(1).strip() if m else None
        if not expr:return None
        expr=expr.replace("×","*").replace("÷","/")
        # Strip prose wrappers that are not part of Python expression.
        expr=re.sub(r"^(?:в\s+python\s+)?","",expr,flags=re.I).strip()
        return expr

    @classmethod
    def _safe_eval_node(cls,node):
        if isinstance(node,ast.Expression):
            return cls._safe_eval_node(node.body)
        if isinstance(node,ast.Constant) and isinstance(node.value,(int,float,str,bool)):
            return node.value
        if isinstance(node,ast.List):
            return [cls._safe_eval_node(x) for x in node.elts]
        if isinstance(node,ast.Tuple):
            return tuple(cls._safe_eval_node(x) for x in node.elts)
        if isinstance(node,ast.UnaryOp) and type(node.op) in cls.SAFE_UNARY:
            return cls.SAFE_UNARY[type(node.op)](cls._safe_eval_node(node.operand))
        if isinstance(node,ast.BinOp) and type(node.op) in cls.SAFE_BINOPS:
            a=cls._safe_eval_node(node.left); b=cls._safe_eval_node(node.right)
            if isinstance(a,(int,float)) and abs(float(a))>1e12: raise ValueError("operand too large")
            if isinstance(b,(int,float)) and abs(float(b))>1e12: raise ValueError("operand too large")
            return cls.SAFE_BINOPS[type(node.op)](a,b)
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in cls.SAFE_CALLS:
            args=[cls._safe_eval_node(x) for x in node.args]
            if node.keywords: raise ValueError("keywords not supported")
            fn=node.func.id
            if fn=="range":
                if not 1<=len(args)<=3: raise ValueError("bad range arity")
                r=list(range(*[int(x) for x in args]))
                if len(r)>100000: raise ValueError("range too large")
                return r
            if fn=="list":
                if len(args)!=1: raise ValueError("bad list arity")
                return list(args[0])
            if fn=="len":
                if len(args)!=1: raise ValueError("bad len arity")
                return len(args[0])
            if fn=="sum":
                if len(args)!=1: raise ValueError("bad sum arity")
                return sum(args[0])
            if fn=="min":
                if len(args)!=1: raise ValueError("bad min arity")
                return min(args[0])
            if fn=="max":
                if len(args)!=1: raise ValueError("bad max arity")
                return max(args[0])
            if fn=="abs":
                if len(args)!=1: raise ValueError("bad abs arity")
                return abs(args[0])
        raise ValueError(f"unsupported AST: {type(node).__name__}")

    @classmethod
    def safe_python_eval(cls,expr:str):
        tree=ast.parse(expr,mode="eval")
        return cls._safe_eval_node(tree)

    @classmethod
    def assess_proof_scope(cls,question:str,proof:dict|None)->str:
        if not proof or proof.get("status")!="VERIFIED" or not proof.get("ir"):
            return "NONE"
        ir=proof["ir"]; rule=str(ir.get("compiler_rule") or "")
        q=cls._norm(question)
        # Known partial-compilation pattern: compiler recognizes inner range while
        # the user requested an outer len/sum/min/max/list composition.
        if rule=="py_range" and any(x in q for x in ("len(","sum(","min(","max(")):
            return "PARTIAL_SCOPE"
        # A compiler source equal to the user query is evidence of full coverage
        # for supported primitive rules.
        if rule in {
            "py_floordiv","arith_mul","arith_add","arith_sub","arith_div",
            "gcd","logic_modus_ponens","py_len","py_sum"
        }:
            return "FULL_SCOPE"
        # Conservative default: exact proof is useful evidence but not final authority.
        return "PARTIAL_SCOPE"

    def decide(self,question:str)->AuthorityDecision:
        sem=self.exact.semantic_answer(question,min_similarity=.55)
        proof=self.exact.proof(question)
        scope=self.assess_proof_scope(question,proof)

        atom_id=sem.get("atom_id") if sem else None
        atom_correct=sem.get("governor_correct") if sem else None
        sem_answer=sem.get("answer") if sem else None
        proof_answer=proof.get("conclusion") if proof else None
        conflict=(sem is not None and proof is not None and str(sem_answer)!=str(proof_answer))

        trace=[]
        if sem:
            trace += [
                f"r76_atom={atom_id}",
                f"r76_governor_correct={atom_correct}",
                f"r76_similarity={sem.get('similarity',0):.3f}",
            ]
        if proof:
            trace += [
                f"r710_status={proof.get('status')}",
                f"r710_rule={(proof.get('ir') or {}).get('compiler_rule')}",
                f"proof_scope={scope}",
            ]

        # A known-wrong frozen atom remains provenance only.
        if sem is not None and atom_correct is False:
            trace.append("r76=QUARANTINED_KNOWN_WRONG")

        if proof and proof.get("status")=="VERIFIED" and scope=="FULL_SCOPE":
            return AuthorityDecision(
                status="RESOLVED", answer=proof_answer,
                authority="R710_VERIFIED_FULL_SCOPE", proof_scope=scope,
                semantic_atom_id=atom_id, semantic_governor_correct=atom_correct,
                conflict=conflict, trace=tuple(trace)
            )

        if proof and proof.get("status")=="VERIFIED" and scope=="PARTIAL_SCOPE":
            expr=self._extract_python_expression(question)
            if expr:
                try:
                    full=self.safe_python_eval(expr)
                    trace.append(f"composed_expression={expr}")
                    trace.append("composition=SAFE_EXECUTED")
                    return AuthorityDecision(
                        status="RESOLVED", answer=full,
                        authority="COMPOSED_VERIFIED_EXECUTION", proof_scope=scope,
                        semantic_atom_id=atom_id, semantic_governor_correct=atom_correct,
                        conflict=conflict, trace=tuple(trace)
                    )
                except Exception as e:
                    trace.append(f"composition_failed={type(e).__name__}")
            return AuthorityDecision(
                status="ABSTAIN", answer=None,
                authority="PARTIAL_PROOF_FAIL_CLOSED", proof_scope=scope,
                semantic_atom_id=atom_id, semantic_governor_correct=atom_correct,
                conflict=conflict, trace=tuple(trace)
            )

        if sem and atom_correct is True:
            trace.append("r76=ACCEPTED_FROZEN_ADVISORY")
            return AuthorityDecision(
                status="RESOLVED", answer=sem_answer,
                authority="R76_ACCEPTED_FROZEN_SEMANTIC", proof_scope="NONE",
                semantic_atom_id=atom_id, semantic_governor_correct=True,
                conflict=False, trace=tuple(trace)
            )

        if sem and atom_correct is False:
            return AuthorityDecision(
                status="ABSTAIN", answer=None,
                authority="QUARANTINED_SEMANTIC_NO_PROOF", proof_scope="NONE",
                semantic_atom_id=atom_id, semantic_governor_correct=False,
                conflict=False, trace=tuple(trace)
            )

        return AuthorityDecision(status="ABSTAIN",trace=tuple(trace))
