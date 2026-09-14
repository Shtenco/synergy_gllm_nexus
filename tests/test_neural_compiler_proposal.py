from nexus_gllm.compiler_proposal import NeuralParseProposal, ProposalValidator


def test_validator_accepts_exact_supported_span_proposal():
    text = "Антон старше Бориса"
    proposal = NeuralParseProposal(
        relation="older_than",
        subject_text="Антон",
        object_text="Бориса",
        subject_span=(0, 5),
        object_span=(13, 19),
        confidence=0.99,
        kind="statement",
    )
    result = ProposalValidator().validate(text, proposal)
    assert result.accepted is True
    assert result.reason == "accepted"


def test_validator_rejects_span_text_mismatch():
    text = "Антон старше Бориса"
    proposal = NeuralParseProposal(
        relation="older_than",
        subject_text="Борис",
        object_text="Антон",
        subject_span=(0, 5),
        object_span=(13, 19),
        confidence=0.99,
        kind="statement",
    )
    result = ProposalValidator().validate(text, proposal)
    assert result.accepted is False
    assert "span" in result.reason


def test_validator_rejects_low_confidence_mutation():
    text = "Москва находится в России"
    proposal = NeuralParseProposal(
        relation="located_in",
        subject_text="Москва",
        object_text="России",
        subject_span=(0, 6),
        object_span=(20, 26),
        confidence=0.49,
        kind="statement",
    )
    result = ProposalValidator(default_threshold=0.8).validate(text, proposal)
    assert result.accepted is False
    assert result.reason == "confidence_below_threshold"


def test_validator_accepts_explicit_abstention_without_spans():
    proposal = NeuralParseProposal(
        relation="abstain",
        subject_text=None,
        object_text=None,
        subject_span=None,
        object_span=None,
        confidence=0.93,
        kind="abstain",
    )
    result = ProposalValidator().validate("Расскажи что-нибудь красивое", proposal)
    assert result.accepted is True
    assert result.is_abstention is True


def test_validator_rejects_invalid_self_loop_for_older_than():
    text = "Антон старше Антона"
    proposal = NeuralParseProposal(
        relation="older_than",
        subject_text="Антон",
        object_text="Антона",
        subject_span=(0, 5),
        object_span=(13, 19),
        confidence=0.99,
        kind="statement",
    )
    result = ProposalValidator().validate(text, proposal)
    assert result.accepted is False
    assert result.reason == "invalid_self_loop"
