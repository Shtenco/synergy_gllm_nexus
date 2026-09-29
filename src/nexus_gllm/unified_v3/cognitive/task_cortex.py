from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
import hashlib,re

from nexus_gllm.unified_v3.contracts import TaskOpcode,TaskProgram
from .language_cortex import SourceSpanRef


@dataclass(frozen=True)
class TaskProposal:
    input_sha256:str
    backend_id:str
    opcode:TaskOpcode
    operator_id:str|None
    arguments:tuple[str,...]
    confidence:float
    source_span:SourceSpanRef


@dataclass(frozen=True)
class TaskAdmission:
    accepted:bool
    reasons:tuple[str,...]


@dataclass(frozen=True)
class TaskParseResult:
    task:TaskProgram|None
    backend_id:str
    input_sha256:str
    source_span:SourceSpanRef|None
    admission:TaskAdmission
    proposal_only:bool=True


class TaskCortexBackend(Protocol):
    backend_id:str
    def propose_task(self,text:str)->TaskProposal: ...


class TaskProposalGate:
    def __init__(self,*,min_confidence=.80,max_args=8):
        self.min_confidence=float(min_confidence);self.max_args=int(max_args)

    @staticmethod
    def digest(text,start,end):
        return hashlib.sha256(text[start:end].encode('utf-8')).hexdigest()

    def check(self,p:TaskProposal,text:str,expected_hash:str)->TaskAdmission:
        reasons=[]
        if p.input_sha256!=expected_hash:reasons.append('input_hash_mismatch')
        if not p.backend_id:reasons.append('backend_id_missing')
        if not 0<=p.confidence<=1 or p.confidence<self.min_confidence:reasons.append('low_confidence')
        if len(p.arguments)>self.max_args:reasons.append('too_many_arguments')
        if p.operator_id is not None and not re.fullmatch(r'[A-Za-zА-Яа-яЁё0-9_.:-]{1,128}',p.operator_id):reasons.append('bad_operator_id')
        if any((not a) or len(a)>256 or any(ord(c)<32 for c in a) for a in p.arguments):reasons.append('bad_argument')
        s=p.source_span;n=len(text)
        if s.start<0 or s.end<=s.start or s.end>n:reasons.append('bad_span_bounds')
        elif self.digest(text,s.start,s.end)!=s.sha256:reasons.append('span_hash_mismatch')
        if p.opcode in (TaskOpcode.QUERY_RELATION,TaskOpcode.FIND_PROOF,TaskOpcode.FIND_MINIMAL_PROOF) and (not p.operator_id or len(p.arguments)!=2):
            reasons.append('relation_query_shape_mismatch')
        return TaskAdmission(not reasons,tuple(sorted(set(reasons))))


class TaskCortexPort:
    def __init__(self,backend:TaskCortexBackend,gate=None):
        self.backend=backend;self.gate=gate or TaskProposalGate()
    @staticmethod
    def input_sha(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
    def parse(self,text):
        h=self.input_sha(text)
        try:
            p=self.backend.propose_task(text)
        except Exception as exc:
            backend_id=getattr(self.backend,'backend_id',type(self.backend).__name__)
            return TaskParseResult(None,backend_id,h,None,TaskAdmission(False,(f'backend_exception:{type(exc).__name__}',)),True)
        a=self.gate.check(p,text,h)
        task=None if not a.accepted else TaskProgram(p.opcode,p.operator_id,tuple(x.casefold() for x in p.arguments))
        return TaskParseResult(task,p.backend_id,h,p.source_span if a.accepted else None,a,True)


class ControlledTaskBackend:
    """Tiny deterministic baseline; future neural intent cortex uses same contract."""
    backend_id='controlled_task_v1'
    PATTERNS=(
      re.compile(r'^Есть ли отношение ([\w:.-]+) от ([\wА-Яа-яЁё-]+) к ([\wА-Яа-яЁё-]+)\??$',re.I|re.U),
      re.compile(r'^Связан ли ([\wА-Яа-яЁё-]+) с ([\wА-Яа-яЁё-]+) отношением ([\w:.-]+)\??$',re.I|re.U),
    )
    def propose_task(self,text):
        clean=text.strip()
        for i,pat in enumerate(self.PATTERNS):
            m=pat.match(clean)
            if not m:continue
            if i==0:op,a,b=m.group(1),m.group(2),m.group(3)
            else:a,b,op=m.group(1),m.group(2),m.group(3)
            h=hashlib.sha256(text.encode()).hexdigest();s=SourceSpanRef(0,len(text),h)
            return TaskProposal(h,self.backend_id,TaskOpcode.QUERY_RELATION,op,(a,b),1.0,s)
        h=hashlib.sha256(text.encode()).hexdigest();s=SourceSpanRef(0,len(text),h)
        return TaskProposal(h,self.backend_id,TaskOpcode.QUERY_RELATION,None,(),0.0,s)
