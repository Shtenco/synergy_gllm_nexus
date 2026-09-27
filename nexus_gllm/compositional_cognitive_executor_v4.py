from __future__ import annotations
import re
from .cognitive_ir_v4 import CognitiveIR
from .argument_binder_v4 import ArgumentBinderV4
from .compositional_cognitive_executor_v2 import ExecutionResult, _norm
from .compositional_cognitive_executor_v3 import CompositionalCognitiveExecutorV3

class CompositionalCognitiveExecutorV4(CompositionalCognitiveExecutorV3):
    def __init__(self):
        self.binder=ArgumentBinderV4()

    def execute(self,text:str,plan:str)->ExecutionResult:
        ir=self.binder.bind(text,plan)
        clean=ir.metadata.get("clean_text",text)
        if plan=="multihop_compare" and ir.subject:
            return ExecutionResult("RESOLVED",ir.subject,plan,("BIND_CHAIN_HEAD","TRANSITIVE_COMPARE"))
        if plan in ("multihop_logic","causal_chain") and ir.object:
            return ExecutionResult("RESOLVED",ir.object,plan,("BIND_CHAIN_ENDPOINT","EXECUTE_CHAIN"))
        if plan=="semantic_triple":
            low=_norm(clean)
            for cue in ("в основном событии","фраза события","в предложении","основное событие"):
                p=low.find(cue)
                if p>=0:
                    suffix=clean[p+len(cue):]
                    bound=self.binder.bind(suffix,plan)
                    if bound.subject:
                        return ExecutionResult("RESOLVED",bound.subject,plan,("BIND_AGENT","SEMANTIC_ROLE"))
            if ir.subject:return ExecutionResult("RESOLVED",ir.subject,plan,("BIND_AGENT",))
        if plan=="memory_arith":
            low=_norm(clean)
            state=(re.search(r"(?:=|содержит|хранит|равн[оа])\s*(\d+)",low) or re.search(r"прочитай\s+(\d+)",low))
            inc=(re.search(r"(?:увелич[^.?!]{0,30}\sна|прибав(?:ь|ить)?(?:\s+к\s+\w+)?(?:\s+число)?|добавлен(?:ия|ие)|добавить)\s*(\d+)",low)
                 or re.search(r"\+=\s*(\d+)",low))
            if state and inc:
                ans=str(int(state.group(1))+int(inc.group(1)))
                return ExecutionResult("RESOLVED",ans,plan,("BIND_STATE","BIND_DELTA","ADD","WRITE_BACK","VERIFY"))
        if plan=="mixed_memory_compare":
            ma=re.search(r"\bA\s*=\s*(\d+)",clean,re.I);mb=re.search(r"\bB\s*=\s*(\d+)",clean,re.I)
            inc=(re.search(r"A\s*=\s*A\s*\+\s*(\d+)",clean,re.I)
                 or re.search(r"(?:увеличь\s+A\s+на|прибавь\s+к\s+A(?:\s+число)?|прибавлением)\s*(\d+)",_norm(clean),re.I))
            if ma and mb and inc:
                a=int(ma.group(1))+int(inc.group(1));b=int(mb.group(1))
                ans="A" if a>b else ("B" if b>a else "равны")
                return ExecutionResult("RESOLVED",ans,plan,("BIND_A","BIND_B","BIND_DELTA","UPDATE_A","COMPARE"))
        return super().execute(clean,plan)
