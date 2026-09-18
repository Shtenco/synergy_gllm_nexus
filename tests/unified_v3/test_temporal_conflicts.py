from nexus_gllm.unified_v3.temporal import TemporalLedger
from nexus_gllm.unified_v3.conflicts import ConflictEngine
from nexus_gllm.unified_v3.contracts import FactLifecycle, ConflictResolution
def test_temporal_revision_preserves_history_and_changes_current():
    l=TemporalLedger(); l=l.assert_fact('owner','car','anna',10); l=l.assert_fact('owner','car','boris',40,supersede=True)
    assert l.current('owner','car').value=='boris'
    assert l.at('owner','car',20).value=='anna'
    assert l.versions[0].lifecycle is FactLifecycle.SUPERSEDED
def test_conflict_is_not_last_write_wins():
    assert ConflictEngine().resolve((('s1',True),('s2',False))).resolution is ConflictResolution.CONFLICTED
