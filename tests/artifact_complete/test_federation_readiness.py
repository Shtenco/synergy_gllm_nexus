from pathlib import Path
from nexus_gllm.unified_v3.moe.exact_artifacts import ArtifactCatalog,ArtifactStatus
from nexus_gllm.unified_v3.moe.federation_readiness import historical_readiness,operational_readiness,mounted_readiness

def test_recovered_r7443_is_exact_deployed_runtime():
    r=ArtifactCatalog.default(Path('/mnt/data')).verify('r7443')
    assert r.status is ArtifactStatus.EXACT_DEPLOYED_RUNTIME

def test_r13x_v3_is_verified_operational_authority_runtime():
    r=ArtifactCatalog.default(Path('/mnt/data')).verify('r13x_v3')
    assert r.status is ArtifactStatus.VERIFIED_OPERATIONAL_RUNTIME

def test_historical_and_operational_counts_are_canonical_not_host_mount_state():
    h=historical_readiness(Path('/mnt/data'));o=operational_readiness(Path('/mnt/data'))
    assert h.count==10 and h.required==11 and h.blockers==('unified_r13',)
    assert o.count==11 and o.required==11 and o.ready and not o.blockers
    assert ('authority_slot','r13x_v3','VERIFIED_OPERATIONAL_RUNTIME') in o.slots

def test_mounted_readiness_reports_missing_external_bytes_without_rewriting_canonical_status():
    m=mounted_readiness(Path('/definitely/not/mounted'))
    assert m.mode=='mounted_operational' and m.count<11 and not m.ready
    assert operational_readiness(Path('/definitely/not/mounted')).ready
