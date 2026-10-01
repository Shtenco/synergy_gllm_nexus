from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

from nexus_gllm.unified_v3.contracts import TaskProgram
from .generalized_ingress import GeneralizedIngressRequest, GroundedSpanRef
from .program_ast import ProgramKind, ProgramNode
from .reasoning_context import ReasoningContextView


@dataclass(frozen=True)
class ProgramProposal:
    node: ProgramNode
    confidence: float
    supporting_spans: tuple[GroundedSpanRef, ...]


@dataclass(frozen=True)
class ProgramAdmission:
    accepted: bool
    reasons: tuple[str, ...] = ()


def decode_program_node(payload: dict[str, Any]) -> ProgramNode:
    if not isinstance(payload, dict): raise ValueError('program_payload_not_object')
    try: kind=ProgramKind(payload['kind'])
    except Exception as exc: raise ValueError('unknown_program_kind') from exc
    symbol=payload.get('symbol','')
    if not isinstance(symbol,str): raise ValueError('program_symbol_not_string')
    raw_params=payload.get('params',[])
    if not isinstance(raw_params,(list,tuple)): raise ValueError('program_params_not_sequence')
    params=[]
    for item in raw_params:
        if not isinstance(item,(list,tuple)) or len(item)!=2: raise ValueError('program_param_not_pair')
        key,value=item
        if not isinstance(key,str) or not isinstance(value,str): raise ValueError('program_param_not_string_pair')
        params.append((key,value))
    raw_children=payload.get('children',[])
    if not isinstance(raw_children,(list,tuple)): raise ValueError('program_children_not_sequence')
    return ProgramNode(kind,symbol,tuple(decode_program_node(c) for c in raw_children),tuple(params))


class ProgramProposalGate:
    STRUCTURAL_BUILTINS=frozenset()
    def __init__(self,*,min_confidence=.80,max_depth=6,max_nodes=64):
        self.min_confidence=float(min_confidence);self.max_depth=int(max_depth);self.max_nodes=int(max_nodes)
    @staticmethod
    def _node_count(node): return 1+sum(ProgramProposalGate._node_count(c) for c in node.children)
    @staticmethod
    def _span_reasons(span,request,label):
        source=request.source_map.get(span.source_id)
        if source is None:return [f'{label}:unknown_source_id']
        if span.start<0 or span.end<=span.start or span.end>len(source.text):return [f'{label}:bad_span_bounds']
        actual=hashlib.sha256(source.text[span.start:span.end].encode('utf-8')).hexdigest()
        return [] if actual==span.sha256 else [f'{label}:span_hash_mismatch']
    @staticmethod
    def _operators_from_atom(node):
        if node.kind is not ProgramKind.ATOM:return ()
        parts=node.symbol.split(':')
        if len(parts)<3 or parts[0]!='rule':return ()
        family=parts[1].lower()
        if family in ('transitive','symmetric') and len(parts)==3:return (parts[2],)
        if family=='inverse' and len(parts)==4:return (parts[2],parts[3])
        if family=='composition' and len(parts)==5:return (parts[2],parts[3],parts[4])
        return ()
    @classmethod
    def _referenced_operators(cls,node):
        out=set(cls._operators_from_atom(node));params=dict(node.params)
        for key in ('operator','query_operator'):
            if key in params: out.add(params[key])
        for child in node.children: out.update(cls._referenced_operators(child))
        return out
    @classmethod
    def _shape_reasons(cls,node):
        reasons=[]
        if node.kind is ProgramKind.ATOM and not cls._operators_from_atom(node): reasons.append('malformed_atom')
        for child in node.children: reasons.extend(cls._shape_reasons(child))
        return reasons
    @staticmethod
    def _context_operators(context): return {f.operator.operator_id for f in context.execution_world.facts}
    def check(self,proposal,request,task,context):
        reasons=[]
        if not (0.0<=proposal.confidence<=1.0) or proposal.confidence<self.min_confidence: reasons.append('low_confidence')
        if proposal.node.depth>self.max_depth: reasons.append('max_depth_exceeded')
        if self._node_count(proposal.node)>self.max_nodes: reasons.append('max_nodes_exceeded')
        reasons.extend(self._shape_reasons(proposal.node))
        if not proposal.supporting_spans: reasons.append('missing_provenance')
        for i,span in enumerate(proposal.supporting_spans): reasons.extend(self._span_reasons(span,request,f'span_{i}'))
        allowed=self._context_operators(context)|set(self.STRUCTURAL_BUILTINS)
        if task.operator_id: allowed.add(task.operator_id)
        for operator_id in sorted(self._referenced_operators(proposal.node)):
            if operator_id not in allowed: reasons.append(f'ungrounded_operator:{operator_id}')
        return ProgramAdmission(not reasons,tuple(sorted(set(reasons))))
