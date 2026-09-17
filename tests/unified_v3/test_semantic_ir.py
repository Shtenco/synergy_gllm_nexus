from dataclasses import dataclass
import pytest
from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, SemanticAtom, SemanticObservation
from nexus_gllm.unified_v3.semantic_ir import assert_text_quarantined, semantic_fingerprint

def test_semantic_fingerprint_ignores_duplicate_construction_but_not_argument_order():
    a=SemanticObservation((SemanticAtom(OperatorSymbol('op:x',2),(Entity('e:a'),Entity('e:b'))),))
    b=SemanticObservation((SemanticAtom(OperatorSymbol('op:x',2),(Entity('e:a'),Entity('e:b'))),))
    c=SemanticObservation((SemanticAtom(OperatorSymbol('op:x',2),(Entity('e:b'),Entity('e:a'))),))
    assert semantic_fingerprint(a)==semantic_fingerprint(b)
    assert semantic_fingerprint(a)!=semantic_fingerprint(c)

def test_reasoning_contract_rejects_raw_text_field():
    @dataclass(frozen=True)
    class Bad: prompt:str
    with pytest.raises(ValueError, match='raw text field'):
        assert_text_quarantined(Bad('leak'))
