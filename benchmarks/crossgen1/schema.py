from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

PANELS=("RU_LANG","GRAPH","REASON","CONTEXT","FAR_TRANSFER","OOD_OVERFIT")

@dataclass(frozen=True)
class CrossGenTask:
    task_id:str
    panel:str
    prompt:Any
    expected:Any
    canonical:dict[str,Any]
    meta:dict[str,Any]
    def to_dict(self): return asdict(self)
