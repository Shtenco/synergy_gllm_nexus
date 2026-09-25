from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import hashlib
from .contracts import ExpertSpec,ExpertMode
class ExpertRegistry:
    def __init__(self): self._specs={}
    def register(self,spec:ExpertSpec): self._specs[spec.expert_id]=spec; return self
    def get(self,expert_id): return self._specs[expert_id]
    def active(self): return tuple(s for s in self._specs.values() if s.active_mode is ExpertMode.ACTIVE)
    def shadow(self): return tuple(s for s in self._specs.values() if s.active_mode is ExpertMode.SHADOW)
    def all(self): return tuple(self._specs.values())
    def verify_artifact(self,expert_id):
        s=self.get(expert_id)
        if not s.artifact_path or not s.artifact_sha256: return True
        p=Path(s.artifact_path)
        ok=p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==s.artifact_sha256
        if not ok: self._specs[expert_id]=replace(s,active_mode=ExpertMode.DISABLED)
        return ok
