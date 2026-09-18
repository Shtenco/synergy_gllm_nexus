from nexus_gllm.unified_v3.contracts import *
def test_p01_contracts_exist_and_p0_opcode_preserved():
    assert TaskOpcode.QUERY_RELATION.value=='query_relation'
    assert HypothesisStatus.ACTIVE.value=='ACTIVE'
    assert FactLifecycle.SUPERSEDED.value=='SUPERSEDED'
    assert PredictionOutcome.REFUTED.value=='REFUTED'
    assert InterventionKind.REMOVE_FACT.value=='REMOVE_FACT'
