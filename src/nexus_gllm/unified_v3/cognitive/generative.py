from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import re

from nexus_gllm.unified_v3.contracts import EpistemicState


@dataclass(frozen=True)
class SurfaceContract:
    """Authority-owned semantics licensed for natural-language realization."""
    epistemic_state: EpistemicState
    answer_values: tuple[str,...]=()
    entity_names: tuple[str,...]=()
    licensed_numbers: tuple[str,...]=()
    provenance_ids: tuple[str,...]=()
    allow_negation: bool=False
    uncertainty: tuple[str,...]=()


@dataclass(frozen=True)
class SurfaceCandidate:
    text: str
    backend_id: str
    authoritative: bool=False


@dataclass(frozen=True)
class SurfaceGuardResult:
    ok: bool
    violations: tuple[str,...]=()


@dataclass(frozen=True)
class SafeSurfaceResult:
    text: str
    backend_id: str
    guard: SurfaceGuardResult
    used_fallback: bool
    authoritative: bool=False


class GenerativeSurfaceBackend(Protocol):
    backend_id: str
    def generate(self, contract: SurfaceContract) -> str: ...


class DeterministicRussianSurface:
    backend_id='deterministic_v3'
    def generate(self,contract:SurfaceContract)->str:
        if contract.epistemic_state is EpistemicState.DISPROVED:
            return 'Вывод опровергнут.'
        if contract.epistemic_state is EpistemicState.CONFLICTED:
            return 'Обнаружены противоречивые выводы.'
        if contract.epistemic_state is EpistemicState.UNRESOLVED:
            return 'Недостаточно данных для вывода.'
        if contract.answer_values:
            return 'Ответ: ' + ', '.join(contract.answer_values) + '.'
        return 'Вывод подтверждён.'


class SurfaceSemanticGuard:
    """Conservative guard for non-authoritative generated text.

    It prevents generated prose from inventing numbers, flipping polarity or
    introducing title-cased named entities absent from the semantic contract.
    """
    SAFE_CAPS={'Ответ','Вывод','Обнаружены','Недостаточно','Уточнение'}
    def check(self,contract:SurfaceContract,text:str)->SurfaceGuardResult:
        violations=[]
        nums=set(re.findall(r'\d+(?:[.,]\d+)?',text))
        licensed_nums=set(contract.licensed_numbers)
        for v in contract.answer_values:
            licensed_nums.update(re.findall(r'\d+(?:[.,]\d+)?',str(v)))
        if nums-licensed_nums:violations.append('unlicensed_number')

        words=set(re.findall(r'[\w-]+',text.casefold(),re.UNICODE))
        if ('не' in words or 'нет' in words or 'невозможно' in words) and not contract.allow_negation and contract.epistemic_state is EpistemicState.PROVED:
            violations.append('negation_flip')

        licensed={x.casefold() for x in contract.entity_names}
        for v in contract.answer_values:
            licensed.update(re.findall(r'[\w-]+',str(v).casefold(),re.UNICODE))
        caps=set(re.findall(r'\b[А-ЯЁA-Z][\w-]+',text,re.UNICODE))
        unknown=[x for x in caps if x not in self.SAFE_CAPS and x.casefold() not in licensed]
        if unknown:violations.append('unlicensed_entity')

        return SurfaceGuardResult(not violations,tuple(sorted(set(violations))))


class AuthoritySafeGenerativeCortex:
    """Natural-language cortex with zero fact/commit authority."""
    def __init__(self,backend:GenerativeSurfaceBackend,fallback=None,guard=None):
        self.backend=backend
        self.fallback=fallback or DeterministicRussianSurface()
        self.guard=guard or SurfaceSemanticGuard()

    def realize(self,contract:SurfaceContract)->SafeSurfaceResult:
        text=str(self.backend.generate(contract))
        checked=self.guard.check(contract,text)
        if checked.ok:
            return SafeSurfaceResult(text,self.backend.backend_id,checked,False,False)
        safe=self.fallback.generate(contract)
        fallback_check=self.guard.check(contract,safe)
        return SafeSurfaceResult(safe,self.fallback.backend_id,fallback_check,True,False)
