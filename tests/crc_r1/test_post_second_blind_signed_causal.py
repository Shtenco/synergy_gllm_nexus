from nexus_gllm.unified_v3.cognitive.causal_model import (
    CausalEvidence,
    CausalEvidenceKind,
    CausalGraph,
)


def test_negative_intervention_and_counterfactual_identify_negative_effect():
    g = CausalGraph()
    g.add(CausalEvidence("obs", "x", "y", CausalEvidenceKind.OBSERVATIONAL, 0.75, 1.0))
    g.add(CausalEvidence("do", "x", "y", CausalEvidenceKind.INTERVENTIONAL, -0.88, 1.0))
    g.add(CausalEvidence("cf", "x", "y", CausalEvidenceKind.COUNTERFACTUAL, -0.82, 1.0))

    edge = g.edge("x", "y")

    assert edge.identified is True
    assert edge.effect_sign == -1
    assert edge.interventional_signed < 0
    assert edge.counterfactual_signed < 0
    assert edge.causal_agreement > 0.0


def test_positive_causal_evidence_is_not_invalidated_by_opposite_observational_correlation():
    g = CausalGraph()
    g.add(CausalEvidence("obs", "x", "y", CausalEvidenceKind.OBSERVATIONAL, -0.75, 1.0))
    g.add(CausalEvidence("do", "x", "y", CausalEvidenceKind.INTERVENTIONAL, 0.88, 1.0))
    g.add(CausalEvidence("cf", "x", "y", CausalEvidenceKind.COUNTERFACTUAL, 0.82, 1.0))

    edge = g.edge("x", "y")

    assert edge.identified is True
    assert edge.effect_sign == 1
    assert edge.observational_signed < 0
    assert edge.interventional_signed > 0
    assert edge.counterfactual_signed > 0


def test_intervention_counterfactual_disagreement_abstains():
    g = CausalGraph()
    g.add(CausalEvidence("do", "x", "y", CausalEvidenceKind.INTERVENTIONAL, 0.95, 1.0))
    g.add(CausalEvidence("cf", "x", "y", CausalEvidenceKind.COUNTERFACTUAL, -0.95, 1.0))

    edge = g.edge("x", "y")

    assert edge.identified is False
    assert edge.effect_sign == 0
    assert edge.causal_agreement == 0.0
