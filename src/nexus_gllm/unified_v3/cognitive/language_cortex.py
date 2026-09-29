from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import hashlib,re

from nexus_gllm.unified_v3.contracts import Entity,OperatorSymbol,SemanticAtom,SemanticObservation
from nexus_gllm.unified_v3.semantic_ir import assert_text_quarantined
from nexus_gllm.unified_v3.surface import ControlledSurfaceAdapter,SurfaceRequest


@dataclass(frozen=True)
class SourceSpanRef:
    start:int
    end:int
    sha256:str


@dataclass(frozen=True)
class ProposedAtom:
    operator_id:str
    arguments:tuple[str,...]
    polarity:bool
    confidence:float
    source_span:SourceSpanRef


@dataclass(frozen=True)
class LanguageParseProposal:
    input_sha256:str
    backend_id:str
    atoms:tuple[ProposedAtom,...]


@dataclass(frozen=True)
class LanguageAdmission:
    accepted:bool
    reasons:tuple[str,...]


@dataclass(frozen=True)
class LanguageParseResult:
    observation:SemanticObservation
    backend_id:str
    input_sha256:str
    admitted_spans:tuple[SourceSpanRef,...]
    admission:LanguageAdmission
    proposal_only:bool=True


class LanguageCortexBackend(Protocol):
    backend_id:str
    def propose(self,text:str)->LanguageParseProposal: ...


class LanguageProposalGate:
    def __init__(self,*,min_confidence=.75,max_atoms=32,max_argument_chars=256):
        self.min_confidence=float(min_confidence);self.max_atoms=int(max_atoms);self.max_argument_chars=int(max_argument_chars)

    @staticmethod
    def _span_digest(text:str,start:int,end:int)->str:
        return hashlib.sha256(text[start:end].encode('utf-8')).hexdigest()

    def check(self,proposal:LanguageParseProposal,text:str,expected_input_sha256:str)->LanguageAdmission:
        reasons=[]
        if proposal.input_sha256!=expected_input_sha256:reasons.append('input_hash_mismatch')
        if not proposal.backend_id:reasons.append('backend_id_missing')
        if not proposal.atoms:reasons.append('empty_semantic_proposal')
        if len(proposal.atoms)>self.max_atoms:reasons.append('too_many_atoms')
        n=len(text)
        for i,a in enumerate(proposal.atoms):
            if not re.fullmatch(r'[A-Za-zА-Яа-яЁё0-9_.:-]{1,128}',a.operator_id):reasons.append(f'atom_{i}:bad_operator_id')
            if not a.arguments:reasons.append(f'atom_{i}:zero_arity')
            if any((not x) or len(x)>self.max_argument_chars or any(ord(c)<32 for c in x) for x in a.arguments):reasons.append(f'atom_{i}:bad_argument')
            if not (0.0<=a.confidence<=1.0) or a.confidence<self.min_confidence:reasons.append(f'atom_{i}:low_confidence')
            span=a.source_span
            if span.start<0 or span.end<=span.start or span.end>n:
                reasons.append(f'atom_{i}:bad_span_bounds')
            elif not re.fullmatch(r'[0-9a-f]{64}',span.sha256):
                reasons.append(f'atom_{i}:bad_span_hash')
            elif self._span_digest(text,span.start,span.end)!=span.sha256:
                reasons.append(f'atom_{i}:span_hash_mismatch')
        return LanguageAdmission(not reasons,tuple(sorted(set(reasons))))


class LanguageCortexPort:
    """Free-text parser boundary. IR stays proposal-only and every atom is span-grounded."""
    def __init__(self,backend:LanguageCortexBackend,gate=None):
        self.backend=backend;self.gate=gate or LanguageProposalGate()

    @staticmethod
    def text_sha256(text:str)->str:return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def parse(self,text:str)->LanguageParseResult:
        digest=self.text_sha256(text);proposal=self.backend.propose(text);admission=self.gate.check(proposal,text,digest)
        spans=tuple(a.source_span for a in proposal.atoms) if admission.accepted else ()
        if not admission.accepted:
            return LanguageParseResult(SemanticObservation(()),proposal.backend_id,digest,(),admission,True)
        atoms=tuple(SemanticAtom(OperatorSymbol(a.operator_id,len(a.arguments)),tuple(Entity(x.casefold()) for x in a.arguments),a.polarity) for a in proposal.atoms)
        observation=SemanticObservation(atoms);assert_text_quarantined(observation)
        return LanguageParseResult(observation,proposal.backend_id,digest,spans,admission,True)


class ControlledLanguageBackend:
    backend_id='controlled_v3'
    def __init__(self):self.surface=ControlledSurfaceAdapter()
    def propose(self,text:str)->LanguageParseProposal:
        digest=hashlib.sha256(text.encode('utf-8')).hexdigest();obs=self.surface.parse(SurfaceRequest(text=text))
        full=SourceSpanRef(0,len(text),hashlib.sha256(text.encode('utf-8')).hexdigest());atoms=[]
        for a in obs.atoms:
            args=tuple(x.entity_id if hasattr(x,'entity_id') else str(x) for x in a.arguments)
            atoms.append(ProposedAtom(a.operator.operator_id,args,a.polarity,1.0,full))
        return LanguageParseProposal(digest,self.backend_id,tuple(atoms))
