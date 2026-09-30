from __future__ import annotations
from pathlib import Path
from typing import Any
from .r13x_exact_cognitive_ru_v3 import ExactCognitiveRussianRuntimeV3
from .pretrained_cortex_v8 import StructuredQwen3CortexV8, V8AuthorityBoundary, CognitiveProposalV8

class UnifiedRussianCognitiveRuntimeV8:
    """Pretrained-language cortex under strict NEXUS authority.

    Resolution order:
      1) R1.3-X V3 exact/formal/memory/world authority.
      2) Qwen3 structured semantic proposal.
      3) Independent verifier callback, when supplied.
      4) VERIFIED answer or ABSTAIN. Qwen3 alone is never final authority.
    """
    def __init__(self,*,cortex_backend,artifact_root:str|Path|None=None,memory_path:str|Path|None=None,verifier=None):
        self.core=ExactCognitiveRussianRuntimeV3(memory_path=memory_path,artifact_root=artifact_root)
        self.cortex=StructuredQwen3CortexV8(cortex_backend)
        self.verifier=verifier

    def _verify_proposal(self,text:str,p:CognitiveProposalV8)->tuple[bool,Any,dict]:
        if self.verifier is None:
            return False,None,{"reason":"NO_INDEPENDENT_VERIFIER"}
        r=self.verifier(text,p)
        if isinstance(r,tuple) and len(r)>=2:
            return bool(r[0]),r[1],{"verifier":r[2] if len(r)>2 else None}
        if isinstance(r,dict):
            return bool(r.get("verified")),r.get("answer"),r
        return False,None,{"reason":"INVALID_VERIFIER_RESULT"}

    def answer(self,text:str,session_id:str="default")->dict[str,Any]:
        core=self.core.answer(text,session_id)
        if not getattr(core,"abstained",False):
            return {"authority":"NEXUS_CORE","answer":getattr(core,"text",None) or getattr(core,"answer",None),"core_response":core,"cortex_used":False}

        proposal=self.cortex.propose(text)
        verified,answer,evidence=self._verify_proposal(text,proposal)
        resolved=V8AuthorityBoundary.resolve(verified_answer=answer,verified=verified,proposal=proposal)
        resolved.update({"cortex_used":True,"plan":proposal.plan,"verification":evidence})
        return resolved
