from __future__ import annotations

import hashlib

import pytest

from nexus_gllm.unified_v3.contracts import TaskOpcode
from nexus_gllm.unified_v3.cognitive.generalized_ingress import (
    GeneralizedIngressBackend,
    GeneralizedIngressProposal,
    GeneralizedIngressR1,
    GeneralizedSemanticAtomProposal,
    GeneralizedTaskProposal,
    GroundedSpanRef,
    SourceEnvelope,
    SourceKind,
    TrustClass,
    GeneralizedIngressRequest,
)


def span(source: SourceEnvelope, needle: str) -> GroundedSpanRef:
    start = source.text.index(needle)
    end = start + len(needle)
    return GroundedSpanRef(
        source_id=source.source_id,
        start=start,
        end=end,
        sha256=hashlib.sha256(source.text[start:end].encode("utf-8")).hexdigest(),
    )


class StaticBackend:
    backend_id = "static-m32"

    def __init__(self, proposal=None, exc: Exception | None = None):
        self.proposal = proposal
        self.exc = exc

    def propose(self, request):
        if self.exc:
            raise self.exc
        return self.proposal


def make_request():
    return GeneralizedIngressRequest.from_texts(
        prompt="Есть ли отношение parent от Алиса к Борис?",
        history=("Alice is parent of Bob.",),
        documents=("Документ: Алиса parent Борис.",),
    )


def valid_proposal(request):
    prompt = request.sources[0]
    atom_span = span(prompt, "Алиса")
    task_span = span(prompt, "parent от Алиса к Борис")
    return GeneralizedIngressProposal(
        backend_id="static-m32",
        semantic_atoms=(
            GeneralizedSemanticAtomProposal(
                operator_id="parent",
                arguments=("алиса", "борис"),
                polarity=True,
                confidence=0.99,
                supporting_spans=(atom_span,),
            ),
        ),
        task=GeneralizedTaskProposal(
            opcode=TaskOpcode.QUERY_RELATION,
            operator_id="parent",
            arguments=("алиса", "борис"),
            confidence=0.99,
            supporting_spans=(task_span,),
        ),
        program=None,
    )


def test_from_texts_assigns_deterministic_source_ids_and_hashes():
    a = make_request()
    b = make_request()
    assert tuple(s.source_id for s in a.sources) == ("prompt:0", "history:0", "document:0")
    assert tuple(s.sha256 for s in a.sources) == tuple(s.sha256 for s in b.sources)
    assert tuple(s.source_kind for s in a.sources) == (SourceKind.PROMPT, SourceKind.HISTORY, SourceKind.DOCUMENT)


def test_ru_span_uses_python_character_offsets_not_utf8_byte_offsets():
    request = make_request()
    proposal = valid_proposal(request)
    result = GeneralizedIngressR1(StaticBackend(proposal)).parse(request)
    assert result.admission.accepted
    admitted = result.semantic_atoms[0].supporting_spans[0]
    source = request.source_map[admitted.source_id]
    assert source.text[admitted.start:admitted.end] == "Алиса"
    assert admitted.start != len(source.text[:admitted.start].encode("utf-8"))


def test_valid_en_history_span_is_admitted():
    request = make_request()
    history = request.sources[1]
    history_span = span(history, "Alice is parent of Bob")
    proposal = GeneralizedIngressProposal(
        backend_id="static-m32",
        semantic_atoms=(
            GeneralizedSemanticAtomProposal("parent", ("alice", "bob"), True, 0.95, (history_span,)),
        ),
        task=valid_proposal(request).task,
        program=None,
    )
    result = GeneralizedIngressR1(StaticBackend(proposal)).parse(request)
    assert result.admission.accepted
    assert result.semantic_atoms[0].supporting_spans == (history_span,)


def test_duplicate_source_ids_fail_closed():
    text = "x"
    digest = hashlib.sha256(text.encode()).hexdigest()
    duplicate = SourceEnvelope("dup", SourceKind.PROMPT, 0, text, digest, TrustClass.USER_ASSERTED)
    request = GeneralizedIngressRequest((duplicate, duplicate))
    result = GeneralizedIngressR1(StaticBackend(None)).parse(request)
    assert not result.admission.accepted
    assert "duplicate_source_id" in result.admission.reasons
    assert result.semantic_atoms == () and result.task is None and result.program is None


def test_unknown_source_id_fails_closed():
    request = make_request()
    bad = GroundedSpanRef("missing:9", 0, 1, "0" * 64)
    proposal = GeneralizedIngressProposal(
        backend_id="static-m32",
        semantic_atoms=(GeneralizedSemanticAtomProposal("r", ("a", "b"), True, 0.99, (bad,)),),
        task=valid_proposal(request).task,
        program=None,
    )
    result = GeneralizedIngressR1(StaticBackend(proposal)).parse(request)
    assert not result.admission.accepted
    assert any("unknown_source_id" in x for x in result.admission.reasons)


@pytest.mark.parametrize("mutation", ["bounds", "hash"])
def test_invalid_span_bounds_or_hash_fail_closed(mutation):
    request = make_request()
    prompt = request.sources[0]
    good = span(prompt, "Алиса")
    bad = (
        GroundedSpanRef(prompt.source_id, -1, good.end, good.sha256)
        if mutation == "bounds"
        else GroundedSpanRef(prompt.source_id, good.start, good.end, "f" * 64)
    )
    proposal = GeneralizedIngressProposal(
        backend_id="static-m32",
        semantic_atoms=(GeneralizedSemanticAtomProposal("r", ("a", "b"), True, 0.99, (bad,)),),
        task=valid_proposal(request).task,
        program=None,
    )
    result = GeneralizedIngressR1(StaticBackend(proposal)).parse(request)
    assert not result.admission.accepted
    assert result.semantic_atoms == () and result.task is None


def test_backend_exception_fails_closed_without_partial_outputs():
    request = make_request()
    result = GeneralizedIngressR1(StaticBackend(exc=RuntimeError("boom"))).parse(request)
    assert not result.admission.accepted
    assert result.admission.reasons == ("backend_exception:RuntimeError",)
    assert result.semantic_atoms == ()
    assert result.task is None
    assert result.program is None


def test_non_enum_task_opcode_fails_closed():
    request = make_request()
    proposal = valid_proposal(request)
    invalid_task = GeneralizedTaskProposal(
        opcode="query_relation",  # type: ignore[arg-type]
        operator_id=proposal.task.operator_id,
        arguments=proposal.task.arguments,
        confidence=proposal.task.confidence,
        supporting_spans=proposal.task.supporting_spans,
    )
    result = GeneralizedIngressR1(
        StaticBackend(
            GeneralizedIngressProposal(
                backend_id=proposal.backend_id,
                semantic_atoms=proposal.semantic_atoms,
                task=invalid_task,
                program=None,
            )
        )
    ).parse(request)
    assert result.admission.accepted is False
    assert "task:invalid_opcode" in result.admission.reasons
    assert result.task is None
