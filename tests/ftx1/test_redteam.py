from benchmarks.ftx1.schema import FTXCase, FTXGold
from benchmarks.ftx1.redteam import run_veto


def mk(prefix):
    return {'x': [(FTXCase(prefix+str(i),'x',f'Анна хранит отчёт {i}.'), FTXGold(answer='Анна', semantic_key=f's{i}')) for i in range(20)]}


def test_veto_rejects_deliberately_leaky_blind_copy():
    dev = mk('d')
    shadow = mk('s')
    blind = mk('b')
    r = run_veto(dev, shadow, blind)
    assert r.pass_all is False
    assert r.skeleton_overlap_dev > 0.05
    assert r.nearest_template_accuracy > 0.45 or r.exact_template_accuracy > 0.45
