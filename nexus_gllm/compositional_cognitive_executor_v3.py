from __future__ import annotations
from .compositional_cognitive_executor_v2 import CompositionalCognitiveExecutorV2, ExecutionResult, _norm, _known, VALUES, COLORS, STATES
import re

class CompositionalCognitiveExecutorV3(CompositionalCognitiveExecutorV2):
    def execute(self,text:str,plan:str)->ExecutionResult:
        t=_norm(text)
        if plan=="world_transition":
            # Avoid treating question wording such as "какой статус активен?" as an observed state.
            qcut=min([p for p in (t.find("какой"),t.find("каково"),t.find("что актуально")) if p>=0] or [len(t)])
            observed=_known(text[:qcut],STATES)
            ans=observed[-1] if observed else None
            return ExecutionResult("RESOLVED" if ans is not None else "ABSTAIN",ans,plan,("ORDER_EVENTS","CURRENT_STATE"))
        if plan=="evidence":
            missing=any(x in t for x in (
                "нет ни измерен","нет измерен","нет источник","нет никаких",
                "отсутствуют исходные данные","исходные данные отсутствуют",
                "никаких сведений","данных не предоставлено","наблюдений нет"
            ))
            ans="недостаточно данных" if missing else "подтверждено"
            return ExecutionResult("RESOLVED",ans,plan,("EVIDENCE_POLICY_V3",))
        return super().execute(text,plan)
