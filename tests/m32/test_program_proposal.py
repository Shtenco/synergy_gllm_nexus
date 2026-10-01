from __future__ import annotations

import hashlib

from nexus_gllm.unified_v3.contracts import TaskOpcode, TaskProgram, WorldHypothesis
from nexus_gllm.unified_v3.cognitive.generalized_ingress import GeneralizedIngressRequest, GroundedSpanRef
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.cognitive.program_proposal import ProgramProposal, ProgramProposalGate, decode_program_node
from nexus_gllm.unified_v3.cognitive.reasoning_context import ReasoningContextView


def req(): return GeneralizedIngressRequest.from_texts("query parent alice bob")

def sp(request):
    source=request.sources[0]
    return GroundedSpanRef(source.source_id,0,len(source.text),hashlib.sha256(source.text.encode()).hexdigest())

def context_with(*ops):
    from nexus_gllm.unified_v3.contracts import Entity,OperatorSymbol,WorldFact
    facts=tuple(WorldFact(OperatorSymbol(op,2),(Entity('alice'),Entity('bob')),True) for op in ops)
    world=WorldHypothesis('m32',facts)
    return ReasoningContextView(world,world,())

def proposal(node,request,confidence=.99): return ProgramProposal(node,confidence,(sp(request),))

def test_valid_atom_is_admitted_when_operator_is_grounded_in_task():
    r=req();t=TaskProgram(TaskOpcode.QUERY_RELATION,'parent',('alice','bob'));n=ProgramNode(ProgramKind.ATOM,'rule:transitive:parent')
    assert ProgramProposalGate().check(proposal(n,r),r,t,context_with('parent')).accepted

def test_all_supported_higher_order_node_kinds_are_structurally_admitted():
    r=req();t=TaskProgram(TaskOpcode.QUERY_RELATION,'parent',('alice','bob'));a=ProgramNode(ProgramKind.ATOM,'rule:transitive:parent')
    nodes=(ProgramNode(ProgramKind.SEQUENCE,children=(a,a)),ProgramNode(ProgramKind.COMPOSE,children=(a,a)),ProgramNode(ProgramKind.IF,children=(a,a)),ProgramNode(ProgramKind.INHIBIT,children=(a,a)),ProgramNode(ProgramKind.TEMPORAL,children=(a,),params=(('mode','current'),)),ProgramNode(ProgramKind.COUNTERFACTUAL,children=(a,),params=(('kind','ADD_FACT'),('operator','parent'),('src','alice'),('dst','bob'))))
    g=ProgramProposalGate(); assert all(g.check(proposal(n,r),r,t,context_with('parent')).accepted for n in nodes)

def test_excessive_depth_fails_closed():
    r=req();t=TaskProgram(TaskOpcode.QUERY_RELATION,'parent',('alice','bob'));n=ProgramNode(ProgramKind.ATOM,'rule:transitive:parent')
    for _ in range(7): n=ProgramNode(ProgramKind.TEMPORAL,children=(n,),params=(('mode','current'),))
    x=ProgramProposalGate(max_depth=6).check(proposal(n,r),r,t,context_with('parent')); assert not x.accepted and 'max_depth_exceeded' in x.reasons

def test_excessive_node_count_fails_closed():
    r=req();t=TaskProgram(TaskOpcode.QUERY_RELATION,'parent',('alice','bob'));a=ProgramNode(ProgramKind.ATOM,'rule:transitive:parent');n=ProgramNode(ProgramKind.SEQUENCE,children=tuple(a for _ in range(65)))
    x=ProgramProposalGate(max_nodes=64).check(proposal(n,r),r,t,context_with('parent')); assert not x.accepted and 'max_nodes_exceeded' in x.reasons

def test_bad_program_provenance_fails_closed():
    r=req();t=TaskProgram(TaskOpcode.QUERY_RELATION,'parent',('alice','bob'));bad=GroundedSpanRef('missing:9',0,1,'0'*64);p=ProgramProposal(ProgramNode(ProgramKind.ATOM,'rule:transitive:parent'),.99,(bad,))
    x=ProgramProposalGate().check(p,r,t,context_with('parent')); assert not x.accepted and any('unknown_source_id' in q for q in x.reasons)

def test_operator_smuggling_fails_closed():
    r=req();t=TaskProgram(TaskOpcode.QUERY_RELATION,'parent',('alice','bob'));n=ProgramNode(ProgramKind.ATOM,'rule:transitive:secret_operator');x=ProgramProposalGate().check(proposal(n,r),r,t,context_with('parent')); assert not x.accepted and 'ungrounded_operator:secret_operator' in x.reasons

def test_query_operator_override_smuggling_fails_closed():
    r=req();t=TaskProgram(TaskOpcode.QUERY_RELATION,'parent',('alice','bob'));a=ProgramNode(ProgramKind.ATOM,'rule:transitive:parent');n=ProgramNode(ProgramKind.IF,children=(a,a),params=(('query_operator','secret_operator'),('query_src','alice'),('query_dst','bob')))
    x=ProgramProposalGate().check(proposal(n,r),r,t,context_with('parent')); assert not x.accepted and 'ungrounded_operator:secret_operator' in x.reasons

def test_malformed_atom_symbol_fails_closed():
    r=req();t=TaskProgram(TaskOpcode.QUERY_RELATION,'parent',('alice','bob'));n=ProgramNode(ProgramKind.ATOM,'not-a-rule')
    x=ProgramProposalGate().check(proposal(n,r),r,t,context_with('parent')); assert not x.accepted and 'malformed_atom' in x.reasons

def test_low_confidence_fails_closed():
    r=req();t=TaskProgram(TaskOpcode.QUERY_RELATION,'parent',('alice','bob'));n=ProgramNode(ProgramKind.ATOM,'rule:transitive:parent');x=ProgramProposalGate().check(proposal(n,r,.79),r,t,context_with('parent')); assert not x.accepted and 'low_confidence' in x.reasons

def test_decoder_rejects_unknown_kind_and_malformed_payload():
    for p in ({'kind':'TELEPORT','symbol':'x','children':[],'params':[]},{'kind':'ATOM','symbol':42,'children':[],'params':[]}):
        try: decode_program_node(p)
        except ValueError: pass
        else: assert False,p
