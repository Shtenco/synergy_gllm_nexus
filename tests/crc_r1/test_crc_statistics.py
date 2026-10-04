import pytest

from benchmarks.crc_statistics import wilson_interval, wilson_lower


def test_wilson_interval_matches_independent_reference_values():
    lo, hi = wilson_interval(80, 100)
    assert lo == pytest.approx(0.7111708344068411, abs=1e-12)
    assert hi == pytest.approx(0.8666330666689676, abs=1e-12)

    lo, hi = wilson_interval(425, 500)
    assert lo == pytest.approx(0.8160389193683016, abs=1e-12)
    assert hi == pytest.approx(0.8786240423086119, abs=1e-12)


def test_wilson_boundary_cases_are_bounded():
    assert wilson_interval(0, 100)[0] == 0.0
    assert wilson_interval(100, 100)[1] == 1.0


def test_wilson_lower_requires_valid_binomial_counts():
    with pytest.raises(ValueError):
        wilson_lower(0, 0)
    with pytest.raises(ValueError):
        wilson_lower(11, 10)
    with pytest.raises(ValueError):
        wilson_lower(-1, 10)
