import pytest

from benchmarks.crc_scm_oracle import LinearSCMOracle, StructuralEquation


def test_linear_scm_recovers_total_mediated_effect_sign():
    scm = LinearSCMOracle(
        (
            StructuralEquation("x"),
            StructuralEquation("m", (("x", -2.0),)),
            StructuralEquation("y", (("m", 0.5),)),
        )
    )
    assert scm.interventional_effect("x", "y") == pytest.approx(-1.0)
    assert scm.effect_sign("x", "y") == -1


def test_do_intervention_replaces_structural_equation_and_keeps_exogenous_fixed():
    scm = LinearSCMOracle(
        (
            StructuralEquation("x", bias=2.0),
            StructuralEquation("y", (("x", 3.0),), bias=1.0),
        )
    )
    factual = scm.evaluate(exogenous={"x": 0.5, "y": 0.25})
    counterfactual = scm.counterfactual("y", intervention={"x": -1.0}, exogenous={"x": 0.5, "y": 0.25})
    assert factual["x"] == pytest.approx(2.5)
    assert factual["y"] == pytest.approx(8.75)
    assert counterfactual == pytest.approx(-1.75)


def test_scm_rejects_cycles_and_unknown_parents():
    with pytest.raises(ValueError):
        LinearSCMOracle((StructuralEquation("x", (("missing", 1.0),)),))
    with pytest.raises(ValueError):
        LinearSCMOracle(
            (
                StructuralEquation("x", (("y", 1.0),)),
                StructuralEquation("y", (("x", 1.0),)),
            )
        )
