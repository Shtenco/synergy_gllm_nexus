from __future__ import annotations

import hashlib

from nexus_gllm.unified_v3.contracts import TaskOpcode, TaskProgram, WorldHypothesis
from nexus_gllm.unified_v3.cognitive.generalized_ingress import (
    GeneralizedIngressRequest,
    GroundedSpanRef,
)
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode
from nexus_gllm.unified_v3.cognitive.program_proposal import (
    ProgramAdmission,
    ProgramProposal,
    ProgramProposalGate,
    decode_program_node,
)
from nexus_gllm.unified_v3.cognitive.reasoning_context import ReasoningContextView


def req():
    return GeneralizedIngressRequest.from_texts("query parent alice bob")


def sp(request):
    source = request.sources[0]
    return GroundedSpanRef(
        source.source_id,
        0,
        len(source.text),
        hashlib.sha256(source.text.encode()).hexdigest(),
    )


def context_with(*ops):
    from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, WorldFact
    facts = tuple(
        WorldFact(OperatorSymbol(op, 2), (Entity("alice"), Entity("bob")), True)
        for op in ops
    )
    world = WorldHypothesis("m32", facts)
    return ReasoningContextView(world, world, ())


def proposal(node, request, confidence=0.99):
    return ProgramProposal(node=node, confidence=confidence, supporting_spans=(sp(request),))


def test_valid_atom_is_admitted_when_operator_is_grounded_in_task():
    request = req()
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "parent", ("alice", "bob"))
    node = ProgramNode(ProgramKind.ATOM, "rule:transitive:parent")
    result = ProgramProposalGate().check(proposal(node, request), request, task, context_with("parent"))
    assert result.accepted


def test_all_supported_higher_order_node_kinds_are_structurally_admitted():
    request = req()
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "parent", ("alice", "bob"))
    atom = ProgramNode(ProgramKind.ATOM, "rule:transitive:parent")
    nodes = (
        ProgramNode(ProgramKind.SEQUENCE, children=(atom, atom)),
        ProgramNode(ProgramKind.COMPOSE, children=(atom, atom)),
        ProgramNode(ProgramKind.IF, children=(atom, atom)),
        ProgramNode(ProgramKind.INHIBIT, children=(atom, atom)),
        ProgramNode(ProgramKind.TEMPORAL, children=(atom,), params=(("mode", "current"),)),
        ProgramNode(
            ProgramKind.COUNTERFACTUAL,
            children=(atom,),
            params=(("kind", "ADD_FACT"), ("operator", "parent"), ("src", "alice"), ("dst", "bob")),
        ),
    )
    gate = ProgramProposalGate()
    assert all(gate.check(proposal(node, request), request, task, context_with("parent")).accepted for node in nodes)


def test_excessive_depth_fails_closed():
    request = req()
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "parent", ("alice", "bob"))
    node = ProgramNode(ProgramKind.ATOM, "rule:transitive:parent")
    for _ in range(7):
        node = ProgramNode(ProgramKind.TEMPORAL, children=(node,), params=(("mode", "current"),))
    result = ProgramProposalGate(max_depth=6).check(proposal(node, request), request, task, context_with("parent"))
    assert not result.accepted and "max_depth_exceeded" in result.reasons


def test_excessive_node_count_fails_closed():
    request = req()
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "parent", ("alice", "bob"))
    atom = ProgramNode(ProgramKind.ATOM, "rule:transitive:parent")
    node = ProgramNode(ProgramKind.SEQUENCE, children=tuple(atom for _ in range(65)))
    result = ProgramProposalGate(max_nodes=64).check(proposal(node, request), request, task, context_with("parent"))
    assert not result.accepted and "max_nodes_exceeded" in result.reasons


def test_bad_program_provenance_fails_closed():
    request = req()
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "parent", ("alice", "bob"))
    bad = GroundedSpanRef("missing:9", 0, 1, "0" * 64)
    p = ProgramProposal(ProgramNode(ProgramKind.ATOM, "rule:transitive:parent"), 0.99, (bad,))
    result = ProgramProposalGate().check(p, request, task, context_with("parent"))
    assert not result.accepted and any("unknown_source_id" in r for r in result.reasons)


def test_operator_smuggling_fails_closed():
    request = req()
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "parent", ("alice", "bob"))
    node = ProgramNode(ProgramKind.ATOM, "rule:transitive:secret_operator")
    result = ProgramProposalGate().check(proposal(node, request), request, task, context_with("parent"))
    assert not result.accepted and "ungrounded_operator:secret_operator" in result.reasons


def test_query_operator_override_smuggling_fails_closed():
    request = req()
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "parent", ("alice", "bob"))
    atom = ProgramNode(ProgramKind.ATOM, "rule:transitive:parent")
    node = ProgramNode(
        ProgramKind.IF,
        children=(atom, atom),
        params=(("query_operator", "secret_operator"), ("query_src", "alice"), ("query_dst", "bob")),
    )
    result = ProgramProposalGate().check(proposal(node, request), request, task, context_with("parent"))
    assert not result.accepted
    assert "ungrounded_operator:secret_operator" in result.reasons


def test_low_confidence_fails_closed():
    request = req()
    task = TaskProgram(TaskOpcode.QUERY_RELATION, "parent", ("alice", "bob"))
    node = ProgramNode(ProgramKind.ATOM, "rule:transitive:parent")
    result = ProgramProposalGate().check(proposal(node, request, confidence=0.79), request, task, context_with("parent"))
    assert not result.accepted and "low_confidence" in result.reasons


def test_decoder_rejects_unknown_kind_and_malformed_payload():
    for payload in (
        {"kind": "TELEPORT", "symbol": "x", "children": [], "params": []},
        {"kind": "ATOM", "symbol": 42, "children": [], "params": []},
    ):
        try:
            decode_program_node(payload)
        except ValueError:
            pass
        else:
            assert False, payload
