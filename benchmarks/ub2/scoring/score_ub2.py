from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Prediction:
    claims: tuple[str, ...] = ()
    citations: tuple[str, ...] = ()
    clarified: bool = False
    uncertain: bool = False
    guard_mutation: bool = False

@dataclass(frozen=True)
class CaseScore:
    strict_correct: bool
    invalid_citations: tuple[str, ...]
    missing_claims: tuple[str, ...]
    forbidden_present: tuple[str, ...]

@dataclass(frozen=True)
class SuiteScore:
    strict_correct: int
    total: int
    full_score: float
    invalid_citation_count: int
    guard_mutations: int


def score_case(case, pred: Prediction) -> CaseScore:
    required=set(case.contract.required_claims); forbidden=set(case.contract.forbidden_claims); claims=set(pred.claims)
    missing=tuple(sorted(required-claims)); bad=tuple(sorted(forbidden & claims))
    allowed_citations=set(case.metadata.get('evidence_doc_ids', case.contract.required_citations))
    invalid=tuple(c for c in pred.citations if c not in allowed_citations)
    missing_citations=set(case.contract.required_citations)-set(pred.citations)
    ok = not missing and not bad and not invalid and not missing_citations and not pred.guard_mutation
    if case.contract.clarification_required:
        ok = ok and pred.clarified and not pred.claims
    if case.contract.expected_uncertainty:
        ok = ok and pred.uncertain
    return CaseScore(ok, invalid, missing, bad)


def score_suite(cases, predictions) -> SuiteScore:
    strict=0; invalid=0; mut=0
    for case in cases:
        pred=predictions.get(case.case_id, Prediction()); cs=score_case(case,pred)
        strict += int(cs.strict_correct); invalid += len(cs.invalid_citations); mut += int(pred.guard_mutation)
    total=len(cases)
    return SuiteScore(strict,total,strict/total if total else 0.0,invalid,mut)
