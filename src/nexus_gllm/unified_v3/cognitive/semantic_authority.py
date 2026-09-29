from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib

from nexus_gllm.unified_v3.contracts import SemanticAtom,WorldFact,WorldHypothesis,Entity
from .language_cortex import LanguageParseResult


class SemanticFactStatus(str,Enum):
    PROPOSED='PROPOSED'
    ASSERTED_CONTEXT='ASSERTED_CONTEXT'
    VERIFIED='VERIFIED'
    REJECTED='REJECTED'


class AttestationKind(str,Enum):
    FORMAL_PROOF='FORMAL_PROOF'
    EVIDENCE='EVIDENCE'
    USER_ASSERTION='USER_ASSERTION'
    MODEL_PROPOSAL='MODEL_PROPOSAL'


@dataclass(frozen=True)
class SemanticAttestation:
    source_id:str
    lineage_id:str
    kind:AttestationKind
    trust:float
    atom_fingerprint:str
    supports:bool=True
    provenance_id:str=''


@dataclass(frozen=True)
class SemanticCommitDecision:
    atom_fingerprint:str
    status:SemanticFactStatus
    accepted:bool
    reasons:tuple[str,...]
    supporting_sources:tuple[str,...]=()
    supporting_lineages:tuple[str,...]=()


@dataclass(frozen=True)
class SemanticCommitResult:
    world:WorldHypothesis
    decisions:tuple[SemanticCommitDecision,...]
    asserted_context:tuple[SemanticAtom,...]=()


def atom_fingerprint(atom:SemanticAtom)->str:
    args=tuple(getattr(x,'entity_id',str(x)).casefold() for x in atom.arguments)
    body=(atom.operator.operator_id.casefold(),atom.operator.arity,args,bool(atom.polarity))
    return hashlib.sha256(repr(body).encode('utf-8')).hexdigest()


class SemanticCommitGate:
    """Separate language understanding from fact authority.

    VERIFIED requires either:
    - one supporting FORMAL_PROOF attestation, or
    - >= min_evidence_lineages independent supporting EVIDENCE lineages whose
      trust meets min_evidence_trust.

    USER_ASSERTION may become ASSERTED_CONTEXT, never VERIFIED by itself.
    MODEL_PROPOSAL never grants authority.
    """
    def __init__(self,*,min_evidence_lineages=2,min_evidence_trust=.75):
        self.min_evidence_lineages=int(min_evidence_lineages)
        self.min_evidence_trust=float(min_evidence_trust)

    def decide_atom(self,atom:SemanticAtom,attestations)->SemanticCommitDecision:
        fp=atom_fingerprint(atom)
        relevant=tuple(a for a in attestations if a.atom_fingerprint==fp)
        contradictions=tuple(a for a in relevant if not a.supports and a.trust>=self.min_evidence_trust)
        if contradictions:
            return SemanticCommitDecision(fp,SemanticFactStatus.REJECTED,False,('trusted_contradiction',))

        formal=tuple(a for a in relevant if a.supports and a.kind is AttestationKind.FORMAL_PROOF and a.trust>=self.min_evidence_trust)
        if formal:
            return SemanticCommitDecision(
                fp,SemanticFactStatus.VERIFIED,True,('formal_proof',),
                tuple(sorted({a.source_id for a in formal})),
                tuple(sorted({a.lineage_id for a in formal})),
            )

        evidence=tuple(a for a in relevant if a.supports and a.kind is AttestationKind.EVIDENCE and a.trust>=self.min_evidence_trust)
        lineages=tuple(sorted({a.lineage_id for a in evidence if a.lineage_id}))
        if len(lineages)>=self.min_evidence_lineages:
            return SemanticCommitDecision(
                fp,SemanticFactStatus.VERIFIED,True,('independent_evidence',),
                tuple(sorted({a.source_id for a in evidence})),lineages,
            )

        user=tuple(a for a in relevant if a.supports and a.kind is AttestationKind.USER_ASSERTION)
        if user:
            return SemanticCommitDecision(
                fp,SemanticFactStatus.ASSERTED_CONTEXT,False,('user_assertion_only',),
                tuple(sorted({a.source_id for a in user})),
                tuple(sorted({a.lineage_id for a in user if a.lineage_id})),
            )

        return SemanticCommitDecision(fp,SemanticFactStatus.PROPOSED,False,('insufficient_authority',))

    @staticmethod
    def _world_fact(atom:SemanticAtom)->WorldFact:
        args=tuple(x if isinstance(x,Entity) else Entity(str(x)) for x in atom.arguments)
        return WorldFact(atom.operator,args,atom.polarity)

    def commit(self,parse:LanguageParseResult,world:WorldHypothesis,attestations=())->SemanticCommitResult:
        if not parse.admission.accepted or not parse.proposal_only:
            return SemanticCommitResult(world,())
        decisions=[];verified=[];asserted=[]
        for atom in parse.observation.atoms:
            d=self.decide_atom(atom,attestations);decisions.append(d)
            if d.status is SemanticFactStatus.VERIFIED:
                verified.append(self._world_fact(atom))
            elif d.status is SemanticFactStatus.ASSERTED_CONTEXT:
                asserted.append(atom)
        existing={(f.operator.operator_id,tuple(x.entity_id for x in f.arguments),f.polarity) for f in world.facts}
        new=list(world.facts)
        for f in verified:
            key=(f.operator.operator_id,tuple(x.entity_id for x in f.arguments),f.polarity)
            if key not in existing:
                existing.add(key);new.append(f)
        out=WorldHypothesis(world.world_id,tuple(new),world.parent_world_id)
        return SemanticCommitResult(out,tuple(decisions),tuple(asserted))
