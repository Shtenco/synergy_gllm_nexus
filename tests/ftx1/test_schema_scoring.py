from benchmarks.ftx1.schema import FTXCase, FTXGold, FTXPrediction
from benchmarks.ftx1.scoring import score_case, score_suite


def test_runtime_serialization_exposes_no_gold_adjacent_fields():
    case = FTXCase(case_id='x1', track='semantic_rule_induction', prompt='p', history=('h1',), documents=(('d1','text'),), pair_group='g1')
    payload = case.to_runtime_dict()
    assert set(payload) == {'case_id','prompt','history','documents'}
    serialized = repr(payload)
    for forbidden in ('track','pair_group','path_edges','relation','role','answer_index','proof_path','renderer','split'):
        assert forbidden not in serialized


def test_strict_scoring_requires_all_contract_dimensions():
    gold = FTXGold(answer='Alpha', structured=('x','y'), epistemic='PROVED', abstain=False, citations=('d1',))
    good = FTXPrediction(answer=' alpha ', structured=('X','Y'), epistemic='proved', abstain=False, citations=('d1',))
    bad = FTXPrediction(answer='alpha', structured=('x','y'), epistemic='UNRESOLVED', abstain=False, citations=('d1',))
    assert score_case(gold, good).strict is True
    assert score_case(gold, bad).strict is False
    assert score_case(gold, bad).epistemic_ok is False


def test_suite_reports_micro_and_macro_strict():
    pairs = [(FTXCase('a','t1','p'), FTXGold(answer='yes')), (FTXCase('b','t1','p'), FTXGold(answer='no')), (FTXCase('c','t2','p'), FTXGold(answer='z'))]
    preds = {'a': FTXPrediction(answer='yes'), 'b': FTXPrediction(answer='wrong'), 'c': FTXPrediction(answer='z')}
    s = score_suite(pairs, preds)
    assert round(s.full_strict, 6) == round(2/3, 6)
    assert round(s.macro_strict, 6) == 0.75
