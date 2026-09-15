from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NeuralParseProposal:
    relation: str
    subject_text: str | None
    object_text: str | None
    subject_span: tuple[int, int] | None
    object_span: tuple[int, int] | None
    confidence: float
    kind: str

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be within [0,1]")


@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    reason: str
    is_abstention: bool = False


class ProposalValidator:
    DEFAULT_RELATIONS = frozenset({
        "is_a",
        "older_than",
        "located_in",
        "owned_by",
        "before",
        "after",
        "causes",
        "actor",
        "object",
        "abstain",
    })
    SELF_LOOP_FORBIDDEN = frozenset({
        "older_than",
        "before",
        "after",
        "causes",
        "owned_by",
        "located_in",
    })

    def __init__(
        self,
        default_threshold: float = 0.80,
        relation_thresholds: dict[str, float] | None = None,
        allowed_relations: set[str] | frozenset[str] | None = None,
    ) -> None:
        if not 0.0 <= default_threshold <= 1.0:
            raise ValueError("default_threshold must be within [0,1]")
        self.default_threshold = float(default_threshold)
        self.relation_thresholds = dict(relation_thresholds or {})
        self.allowed_relations = frozenset(allowed_relations or self.DEFAULT_RELATIONS)

    @staticmethod
    def _normalized(text: str | None) -> str | None:
        if text is None:
            return None
        return " ".join(text.strip().casefold().split())

    @staticmethod
    def _span_matches(source: str, span: tuple[int, int] | None, expected: str | None) -> bool:
        if span is None or expected is None:
            return False
        start, end = span
        if start < 0 or end <= start or end > len(source):
            return False
        actual = source[start:end]
        return ProposalValidator._normalized(actual) == ProposalValidator._normalized(expected)

    def validate(self, source_text: str, proposal: NeuralParseProposal) -> ValidationResult:
        if proposal.relation not in self.allowed_relations:
            return ValidationResult(False, "unsupported_relation")

        threshold = self.relation_thresholds.get(proposal.relation, self.default_threshold)
        if proposal.confidence < threshold:
            return ValidationResult(False, "confidence_below_threshold")

        if proposal.relation == "abstain" or proposal.kind == "abstain":
            return ValidationResult(True, "accepted", is_abstention=True)

        if not self._span_matches(source_text, proposal.subject_span, proposal.subject_text):
            return ValidationResult(False, "subject_span_mismatch")
        if not self._span_matches(source_text, proposal.object_span, proposal.object_text):
            return ValidationResult(False, "object_span_mismatch")

        if proposal.relation in self.SELF_LOOP_FORBIDDEN:
            subject = self._normalized(proposal.subject_text)
            obj = self._normalized(proposal.object_text)
            # Russian case endings make exact surface equality too strict; strip a final
            # common genitive/accusative vowel only for this safety comparison.
            def stem(value: str | None) -> str:
                if not value:
                    return ""
                if len(value) > 4 and value.endswith(("а", "я")):
                    return value[:-1]
                return value

            if stem(subject) == stem(obj):
                return ValidationResult(False, "invalid_self_loop")

        return ValidationResult(True, "accepted")
