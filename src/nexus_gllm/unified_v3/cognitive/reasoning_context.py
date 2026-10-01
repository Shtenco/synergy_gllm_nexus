from __future__ import annotations

from dataclasses import dataclass

from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, SemanticAtom, WorldFact, WorldHypothesis
from .generalized_ingress import GeneralizedIngressResult, GeneralizedSemanticAtomProposal, TrustClass
from .semantic_authority import (
    AttestationKind,
    SemanticAttestation,
    SemanticCommitGate,
    SemanticFactStatus,
    atom_fingerprint,
)


@dataclass(frozen=True)
class ReasoningFact:
    atom: SemanticAtom
    status: SemanticFactStatus
    source_ids: tuple[str, ...]
    provenance_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReasoningContextView:
    durable_world: WorldHypothesis
    execution_world: WorldHypothesis
    reasoning_facts: tuple[ReasoningFact, ...]


class ReasoningContextBuilder:
    def __init__(self, commit_gate: SemanticCommitGate | None = None):
        self.commit_gate = commit_gate or SemanticCommitGate()

    @staticmethod
    def semantic_atom(proposal: GeneralizedSemanticAtomProposal) -> SemanticAtom:
        return SemanticAtom(
            OperatorSymbol(proposal.operator_id, len(proposal.arguments)),
            tuple(Entity(argument.casefold()) for argument in proposal.arguments),
            proposal.polarity,
        )

    @staticmethod
    def fingerprint(atom: SemanticAtom) -> str:
        return atom_fingerprint(atom)

    @staticmethod
    def _world_fact(atom: SemanticAtom) -> WorldFact:
        return WorldFact(
            atom.operator,
            tuple(argument if isinstance(argument, Entity) else Entity(str(argument)) for argument in atom.arguments),
            atom.polarity,
        )

    @staticmethod
    def _key(fact: WorldFact) -> tuple[str, tuple[str, ...], bool]:
        return (
            fact.operator.operator_id,
            tuple(argument.entity_id for argument in fact.arguments),
            fact.polarity,
        )

    def _source_attestations(
        self,
        proposal: GeneralizedSemanticAtomProposal,
        ingress: GeneralizedIngressResult,
        fingerprint: str,
    ) -> tuple[SemanticAttestation, ...]:
        source_map = ingress.source_map
        attestations = []
        seen = set()
        for span in proposal.supporting_spans:
            source = source_map.get(span.source_id)
            if source is None or source.source_id in seen:
                continue
            seen.add(source.source_id)
            if source.trust_class in (TrustClass.USER_ASSERTED, TrustClass.DOCUMENT_ASSERTED):
                kind = AttestationKind.USER_ASSERTION
                trust = 1.0
            elif source.trust_class is TrustClass.VERIFIED_EVIDENCE:
                kind = AttestationKind.EVIDENCE
                trust = 1.0
            else:
                kind = AttestationKind.MODEL_PROPOSAL
                trust = 0.0
            attestations.append(
                SemanticAttestation(
                    source_id=source.source_id,
                    lineage_id=source.source_id,
                    kind=kind,
                    trust=trust,
                    atom_fingerprint=fingerprint,
                    supports=True,
                    provenance_id=span.sha256,
                )
            )
        return tuple(attestations)

    def build(
        self,
        verified_world: WorldHypothesis,
        ingress: GeneralizedIngressResult,
        attestations: tuple[SemanticAttestation, ...] = (),
    ) -> ReasoningContextView:
        if not ingress.admission.accepted:
            return ReasoningContextView(verified_world, verified_world, ())

        durable_facts = list(verified_world.facts)
        durable_keys = {self._key(fact) for fact in durable_facts}
        asserted_facts: list[WorldFact] = []
        reasoning_facts: list[ReasoningFact] = []
        added_verified = False

        for proposal in ingress.semantic_atoms:
            atom = self.semantic_atom(proposal)
            fingerprint = self.fingerprint(atom)
            auto = self._source_attestations(proposal, ingress, fingerprint)
            decision = self.commit_gate.decide_atom(atom, auto + tuple(attestations))
            fact = self._world_fact(atom)
            source_ids = tuple(sorted({span.source_id for span in proposal.supporting_spans}))
            provenance_ids = tuple(sorted({span.sha256 for span in proposal.supporting_spans}))
            reasoning_facts.append(
                ReasoningFact(atom, decision.status, source_ids, provenance_ids)
            )
            if decision.status is SemanticFactStatus.VERIFIED:
                key = self._key(fact)
                if key not in durable_keys:
                    durable_keys.add(key)
                    durable_facts.append(fact)
                    added_verified = True
            elif decision.status is SemanticFactStatus.ASSERTED_CONTEXT:
                asserted_facts.append(fact)

        durable_world = (
            WorldHypothesis(
                verified_world.world_id,
                tuple(durable_facts),
                verified_world.parent_world_id,
            )
            if added_verified
            else verified_world
        )

        execution_facts = list(durable_world.facts)
        execution_keys = {self._key(fact) for fact in execution_facts}
        for fact in asserted_facts:
            key = self._key(fact)
            if key not in execution_keys:
                execution_keys.add(key)
                execution_facts.append(fact)

        execution_world = (
            durable_world
            if len(execution_facts) == len(durable_world.facts)
            else WorldHypothesis(
                verified_world.world_id + ":m32:execution",
                tuple(execution_facts),
                verified_world.world_id,
            )
        )
        return ReasoningContextView(durable_world, execution_world, tuple(reasoning_facts))
