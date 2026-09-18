from training.v3_meta.universe import SyntheticUniverseGenerator
def test_families_are_disjoint_and_gold_consistent():
    a=SyntheticUniverseGenerator('A',7).generate(50); b=SyntheticUniverseGenerator('B',7).generate(50); c=SyntheticUniverseGenerator('C',7).generate(50)
    assert {x.operator_token for x in a}.isdisjoint({x.operator_token for x in b})
    assert {x.operator_token for x in a}.isdisjoint({x.operator_token for x in c})
    assert all(x.gold_index in range(len(x.candidates)) for x in a+b+c)
