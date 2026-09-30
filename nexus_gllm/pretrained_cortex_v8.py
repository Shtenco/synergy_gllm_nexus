from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from typing import Any, Protocol

@dataclass(frozen=True)
class CognitiveProposalV8:
    plan: str
    answer_candidate: str | None
    subject: str | None = None
    relation: str | None = None
    object: str | None = None
    current_state: str | None = None
    historic_states: tuple[str,...] = ()
    operands: tuple[float,...] = ()
    evidence_needed: bool = False
    confidence: float = 0.0
    raw: dict[str,Any] | None = None
    def to_dict(self): return asdict(self)

class LanguageCortex(Protocol):
    def generate(self,prompt:str,*,system:str,max_tokens:int=384,temperature:float=0.0)->dict[str,Any]: ...

SYSTEM_PROMPT = '''Ты языковой cortex NEXUS. Верни только JSON.
Ты НЕ источник истины и НЕ финальный authority.
Выдели смысл запроса в поля: plan, answer_candidate, subject, relation, object, current_state, historic_states, operands, evidence_needed, confidence.
plan: natural_ru|multi_hop|causal|memory_context|conflicting_memory|world_state|semantic_graph|formal_executable|evidence_epistemic|mixed_cognitive.
Не выдумывай отсутствующие факты. Если данных недостаточно, answer_candidate=null.'''

class StructuredQwen3CortexV8:
    def __init__(self,backend:LanguageCortex): self.backend=backend
    def propose(self,text:str)->CognitiveProposalV8:
        r=self.backend.generate(text,system=SYSTEM_PROMPT,max_tokens=320,temperature=0.0)
        raw_text=str(r.get('text','')).strip()
        if raw_text.startswith('```'):
            raw_text=raw_text.strip('`')
            raw_text=raw_text.removeprefix('json').strip()
        obj=json.loads(raw_text)
        plan=str(obj.get('plan') or '')
        allowed={'natural_ru','multi_hop','causal','memory_context','conflicting_memory','world_state','semantic_graph','formal_executable','evidence_epistemic','mixed_cognitive'}
        if plan not in allowed: raise ValueError(f'unsupported V8 plan: {plan}')
        return CognitiveProposalV8(plan=plan,answer_candidate=obj.get('answer_candidate'),subject=obj.get('subject'),relation=obj.get('relation'),object=obj.get('object'),current_state=obj.get('current_state'),historic_states=tuple(obj.get('historic_states') or ()),operands=tuple(float(x) for x in (obj.get('operands') or ())),evidence_needed=bool(obj.get('evidence_needed',False)),confidence=max(0.0,min(1.0,float(obj.get('confidence',0.0)))),raw=obj)

class V8AuthorityBoundary:
    PROPOSAL_ONLY='QWEN3_PROPOSAL_ONLY'
    VERIFIED='NEXUS_VERIFIED'
    ABSTAIN='NEXUS_ABSTAIN'
    @staticmethod
    def resolve(*,verified_answer:Any=None,verified:bool=False,proposal:CognitiveProposalV8|None=None):
        if verified:
            return {'authority':V8AuthorityBoundary.VERIFIED,'answer':verified_answer,'proposal':proposal.to_dict() if proposal else None}
        return {'authority':V8AuthorityBoundary.ABSTAIN,'answer':None,'proposal':proposal.to_dict() if proposal else None}