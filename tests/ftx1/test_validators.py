from benchmarks.ftx1.schema import FTXCase, FTXGold
from benchmarks.ftx1.validators import normalized_skeleton, skeleton_overlap, validate_bundle


def test_normalized_skeleton_abstracts_entities_numbers_and_surface_lexemes():
    a = FTXCase('1','x','Анна передала объект-57 Борису после сигнала Сигма001.')
    b = FTXCase('2','x','Марина вручила предмет-88 Олегу вслед за маркером Омега992.')
    assert normalized_skeleton(a) == normalized_skeleton(b)


def test_overlap_detects_reused_grammar_family():
    a = [(FTXCase(str(i),'x',f'Анна передала объект-{i} Борису после сигнала Сигма{i}.'), FTXGold(answer='x')) for i in range(5)]
    b = [(FTXCase('b'+str(i),'x',f'Ирина вручила предмет-{i+10} Павлу вслед за маркером Омега{i+100}.'), FTXGold(answer='x')) for i in range(5)]
    assert skeleton_overlap(a,b) == 1.0


def test_validator_catches_duplicate_ids_and_bad_pair_semantics():
    c1 = FTXCase('dup','x','p1', pair_group='g')
    c2 = FTXCase('dup','x','p2', pair_group='g')
    bundle = {'x': [(c1, FTXGold(answer='a', semantic_key='S1')), (c2, FTXGold(answer='b', semantic_key='S2'))]}
    errors = validate_bundle(bundle)
    assert any('duplicate case_id' in e for e in errors)
    assert any('pair_group semantic mismatch' in e for e in errors)
