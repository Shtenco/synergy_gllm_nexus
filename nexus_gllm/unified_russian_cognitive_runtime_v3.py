from __future__ import annotations
from pathlib import Path
from typing import Callable
from .r13x_exact_cognitive_ru_v3 import ExactCognitiveRussianRuntimeV3
from .unified_ru_planner_v3 import load_planner
from .compositional_cognitive_executor_v3 import CompositionalCognitiveExecutorV3

class UnifiedRussianCognitiveRuntimeV3:
    def __init__(self,*,planner_checkpoint:str|Path,artifact_root=None,memory_path=None,cortex:Callable[[str],str]|None=None):
        self.core=ExactCognitiveRussianRuntimeV3(memory_path=memory_path,artifact_root=artifact_root)
        self.planner=load_planner(planner_checkpoint)
        self.executor=CompositionalCognitiveExecutorV3()
        self.cortex=cortex
    def answer(self,text:str,session_id:str="default"):
        core=self.core.answer(text,session_id)
        if not getattr(core,"abstained",False):
            return {"authority":"NEXUS_CORE","response":core}
        plan,confidence,distribution=self.planner.predict(text)
        out=self.executor.execute(text,plan)
        if out.status=="RESOLVED":
            return {"authority":"COMPOSITIONAL_EXECUTOR_V3","answer":out.answer,"plan":plan,"confidence":confidence,"trace":out.trace}
        proposal=self.cortex(text) if self.cortex is not None else None
        return {"authority":"ABSTAIN","cortex_proposal":proposal,"plan":plan,"confidence":confidence}
