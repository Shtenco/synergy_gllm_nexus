from __future__ import annotations
from pathlib import Path

from .r13x_cognitive_ru import CognitiveRUResponse, ParsedRU, _norm
from .r13x_exact_cognitive_ru_v2 import ExactCognitiveRussianRuntimeV2
from .r13x_compositional_authority_v3 import CompositionalAuthorityGovernorV3

class ExactCognitiveRussianRuntimeV3(ExactCognitiveRussianRuntimeV2):
    """V2 dialogue/runtime plus compositional authority arbitration."""

    def __init__(self,memory_path: str|Path|None=None,artifact_root: str|Path|None=None):
        super().__init__(memory_path=memory_path,artifact_root=artifact_root)
        self.comp=CompositionalAuthorityGovernorV3(self.exact_v2) if self.exact_v2 else None

    def _should_consult_compositional(self,text:str)->bool:
        if not self.comp or not self.exact_v2:
            return False
        proof=self.exact_v2.proof(text)
        if proof and proof.get("status")=="VERIFIED":
            return True
        sem=self.exact_v2.semantic_answer(text,min_similarity=.65)
        return sem is not None

    def answer(self,text:str,session_id:str="default")->CognitiveRUResponse:
        # Keep MCQ consensus path from V2 unchanged.
        if self._parse_mcq(text):
            return super().answer(text,session_id)

        if self._should_consult_compositional(text):
            d=self.comp.decide(text)
            if d.status=="RESOLVED":
                p=ParsedRU("compositional_authority",{},.999,_norm(text))
                if d.authority=="R710_VERIFIED_FULL_SCOPE":
                    rendered=f"Проверенный итог: {d.answer}."
                    organ="r710_proof"
                    evidence=("r710_verified_full_scope",)
                elif d.authority=="COMPOSED_VERIFIED_EXECUTION":
                    rendered=f"Проверенный составной итог: {d.answer}."
                    organ="compositional_authority"
                    evidence=("r710_verified_subproof","safe_outer_composition")
                elif d.authority=="R76_ACCEPTED_FROZEN_SEMANTIC":
                    rendered=str(d.answer)
                    organ="r76_semantic_memory"
                    evidence=("r76_accepted_frozen_semantic",)
                else:
                    rendered=str(d.answer)
                    organ="compositional_authority"
                    evidence=("authority_resolved",)
                return self._finish(
                    session_id,p,rendered,evidence=evidence,organ=organ,trace=d.trace
                )

            if d.authority in ("PARTIAL_PROOF_FAIL_CLOSED","QUARANTINED_SEMANTIC_NO_PROOF"):
                p=ParsedRU("compositional_authority",{},.999,_norm(text))
                return self._finish(
                    session_id,p,self.renderer.render("evidence_missing"),
                    abstained=True,
                    evidence=("authority_fail_closed",),
                    organ="compositional_authority",
                    trace=d.trace,
                )

        return super().answer(text,session_id)
