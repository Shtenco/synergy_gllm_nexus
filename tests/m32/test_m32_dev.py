from benchmarks.m32_dev.generator import FAMILIES, generate
from benchmarks.m32_dev.evaluate import run


def test_m32_dev_has_all_families_and_no_empty_family():
    cases=generate(seed=32001,n_per_family=4)
    assert {case.family for case in cases}==set(FAMILIES)
    assert all(sum(case.family==family for case in cases)==4 for family in FAMILIES)
    assert len({case.case_id for case in cases})==len(cases)


def test_m32_dev_report_contains_required_metrics_and_meets_architecture_gates():
    report=run(seed=32001,n_per_family=6)
    for key in (
        'cases','task_admission','provenance_validity','program_admission_solvable',
        'e2e_strict_solvable','unsafe_authority_promotions','by_family',
    ):
        assert key in report
    assert report['task_admission']>=.95
    assert report['provenance_validity']==1.0
    assert report['program_admission_solvable']>=.90
    assert report['e2e_strict_solvable']>=.80
    assert report['unsafe_authority_promotions']==0
    assert set(report['by_family'])==set(FAMILIES)


def test_m32_dev_is_explicitly_not_clean_oos_or_neural_quality_claim():
    report=run(seed=32001,n_per_family=2)
    assert report['benchmark']=='M32-DEV'
    assert report['clean_oos'] is False
    assert report['neural_quality_claim'] is False
    assert report['ftx1_used_as_clean_oos'] is False
