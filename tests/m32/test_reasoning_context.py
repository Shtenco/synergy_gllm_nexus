from __future__ import annotations

import hashlib

from nexus_gllm.unified_v3.contracts import OperatorSymbol, Entity, WorldFact, WorldHypothesis, TaskOpcode
from nexus_gllm.unified_v3.cognitive.generalized_ingress import (
    GeneralizedIngressProposal,
    GeneralizedIngressR1,
    GeneralizedIngressRequest,
    GeneralizedSemanticAtomProposal,
    GeneralizedTaskProposal,
    GroundedSpanRef,
    SourceEnvelope,
    SourceKind,
    TrustClass,
)
from nexus_gllm.unified_v3.cognitive.reasoning_context import ReasoningContextBuilder
from nexus_gllm.unified_v3.cognitive.semantic_authority import (
    AttestationKind,
    SemanticAttestation,
    SemanticFactStatus,
)


class StaticBackend:
    backend_id = "reasoning-context-fixture"

    def __init__(self, proposal):
        self.proposal = proposal

    def propose(self, request):
        return self.proposal


def source(kind, source_id, text, trust):
    return SourceEnvelope(
        source_id,
        kind,
        0,
        text,
        hashlib.sha256(text.encode("utf-8")).hexdigest(),
        trust,
    )


def span(src, needle):
    start = src.text.index(needle)
    end = start + len(needle)
    return GroundedSpanRef(
        src.source_id,
        start,
        end,
        hashlib.sha256(src.text[start:end].encode("utf-8")).hexdigest(),
    )


def ingress_for(sources, spans):
    task_source = sources[0]
    task_span = span(task_source, "query")
    proposal = GeneralizedIngressProposal(
        backend_id="reasoning-context-fixture",
        semantic_atoms=(
            GeneralizedSemanticAtomProposal("parent", ("alice", "bob"), True, 0.99, tuple(spans)),
        ),
        task=GeneralizedTaskProposal(
            TaskOpcode.QUERY_RELATION,
            "parent",
            ("alice", "bob"),
            0.99,
            (task_span,),
        ),
        program=None,
    )
    return GeneralizedIngressR1(StaticBackend(proposal)).parse(GeneralizedIngressRequest(tuple(sources)))


def fact_keys(world):
    return {
        (f.operator.operator_id, tuple(a.entity_id for a in f.arguments), f.polarity)
        for f in world.facts
    }


def test_user_assertion_is_transient_and_does_not_mutate_durable_world():
    prompt = source(SourceKind.PROMPT, "prompt:0", "query alice parent bob", TrustClass.USER_ASSERTED)
    ingress = ingress_for((prompt,), (span(prompt, "alice parent bob"),))
    durable = WorldHypothesis("verified")

    view = ReasoningContextBuilder().build(durable, ingress)

    key = ("parent", ("alice", "bob"), True)
    assert key in fact_keys(view.execution_world)
    assert key not in fact_keys(view.durable_world)
    assert view.durable_world is durable
    assert view.reasoning_facts[0].status is SemanticFactStatus.ASSERTED_CONTEXT


def test_document_assertion_is_also_transient():
    prompt = source(SourceKind.PROMPT, "prompt:0", "query alice parent bob", TrustClass.USER_ASSERTED)
    doc = source(SourceKind.DOCUMENT, "document:0", "alice parent bob", TrustClass.DOCUMENT_ASSERTED)
    ingress = ingress_for((prompt, doc), (span(doc, "alice parent bob"),))

    view = ReasoningContextBuilder().build(WorldHypothesis("verified"), ingress)

    assert view.reasoning_facts[0].status is SemanticFactStatus.ASSERTED_CONTEXT
    assert len(view.execution_world.facts) == 1
    assert len(view.durable_world.facts) == 0


def test_model_only_proposal_is_not_promoted_into_execution_world():
    prompt = source(SourceKind.PROMPT, "prompt:0", "query alice parent bob", TrustClass.USER_ASSERTED)
    model = source(SourceKind.HISTORY, "history:0", "alice parent bob", TrustClass.MODEL_PROPOSAL)
    ingress = ingress_for((prompt, model), (span(model, "alice parent bob"),))

    view = ReasoningContextBuilder().build(WorldHypothesis("verified"), ingress)

    assert view.reasoning_facts[0].status is SemanticFactStatus.PROPOSED
    assert view.execution_world.facts == ()


def test_two_independent_verified_evidence_sources_produce_verified_fact():
    prompt = source(SourceKind.PROMPT, "prompt:0", "query alice parent bob", TrustClass.USER_ASSERTED)
    a = source(SourceKind.DOCUMENT, "document:0", "alice parent bob evidence A", TrustClass.VERIFIED_EVIDENCE)
    b = SourceEnvelope(
        "document:1",
        SourceKind.DOCUMENT,
        1,
        "alice parent bob evidence B",
        hashlib.sha256("alice parent bob evidence B".encode()).hexdigest(),
        TrustClass.VERIFIED_EVIDENCE,
    )
    ingress = ingress_for((prompt, a, b), (span(a, "alice parent bob"), span(b, "alice parent bob")))

    view = ReasoningContextBuilder().build(WorldHypothesis("verified"), ingress)

    assert view.reasoning_facts[0].status is SemanticFactStatus.VERIFIED
    assert len(view.execution_world.facts) == 1
    assert len(view.durable_world.facts) == 1


def test_trusted_contradiction_rejects_asserted_atom():
    prompt = source(SourceKind.PROMPT, "prompt:0", "query alice parent bob", TrustClass.USER_ASSERTED)
    ingress = ingress_for((prompt,), (span(prompt, "alice parent bob"),))
    builder = ReasoningContextBuilder()
    atom = builder.semantic_atom(ingress.semantic_atoms[0])
    fp = builder.fingerprint(atom)
    contradiction = SemanticAttestation(
        source_id="evidence:contradiction",
        lineage_id="lineage:independent",
        kind=AttestationKind.EVIDENCE,
        trust=0.99,
        atom_fingerprint=fp,
        supports=False,
        provenance_id="proof:negative",
    )

    view = builder.build(WorldHypothesis("verified"), ingress, attestations=(contradiction,))

    assert view.reasoning_facts[0].status is SemanticFactStatus.REJECTED
    assert view.execution_world.facts == ()
