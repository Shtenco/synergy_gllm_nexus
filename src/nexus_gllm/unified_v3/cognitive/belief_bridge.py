from __future__ import annotations
from .belief_state import BeliefLedger,BeliefStatus
from .semantic_authority import SemanticCommitResult,SemanticFactStatus

def ingest_semantic_commit(ledger:BeliefLedger,commit:SemanticCommitResult):
    created=[]
    for d in commit.decisions:
        status={
            SemanticFactStatus.VERIFIED:BeliefStatus.VERIFIED,
            SemanticFactStatus.ASSERTED_CONTEXT:BeliefStatus.ASSERTED,
            SemanticFactStatus.REJECTED:BeliefStatus.REJECTED,
            SemanticFactStatus.PROPOSED:BeliefStatus.PROPOSED,
        }[d.status]
        created.append(ledger.add(
            d.atom_fingerprint,
            d.atom_fingerprint,
            status=status,
            confidence=1.0 if status is BeliefStatus.VERIFIED else .6,
            provenance_ids=d.supporting_sources,
        ))
    return tuple(created)
