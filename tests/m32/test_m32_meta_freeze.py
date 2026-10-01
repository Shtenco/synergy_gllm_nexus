from pathlib import Path
import json
import pytest

from benchmarks.m32_dev.generator import FAMILIES as DEV_FAMILIES
from benchmarks.m32_meta.generator import META_FAMILIES, META_SEED, generate, generator_fingerprint
from benchmarks.m32_meta.freeze import build_manifest, write_manifest


def test_meta_generator_is_deterministic_and_independent_from_dev_configuration():
    a=generate(seed=META_SEED,n_per_family=3)
    b=generate(seed=META_SEED,n_per_family=3)
    assert a==b
    assert META_SEED!=32001
    assert set(META_FAMILIES)!=set(DEV_FAMILIES)
    assert len({case.case_id for case in a})==len(a)


def test_meta_manifest_binds_generator_seed_case_count_and_implementation_commit():
    cases=generate(seed=META_SEED,n_per_family=2)
    manifest=build_manifest(
        generator_sha256=generator_fingerprint(),
        seed=META_SEED,
        case_count=len(cases),
        implementation_commit='abc123',
    )
    assert manifest['schema']=='nexus.m32.meta.freeze.v1'
    assert manifest['generator_sha256']==generator_fingerprint()
    assert manifest['seed']==META_SEED
    assert manifest['case_count']==len(cases)
    assert manifest['implementation_commit']=='abc123'
    assert manifest['ftx1_status']=='CONSUMED_FTX1'
    assert manifest['ftx1_used_as_clean_oos'] is False
    assert manifest['test_open_count']==0


def test_sealed_manifest_refuses_changed_generator_or_commit(tmp_path):
    path=tmp_path/'freeze_manifest.json'
    first=build_manifest(generator_sha256='a'*64,seed=META_SEED,case_count=12,implementation_commit='commit-a')
    write_manifest(path,first)
    write_manifest(path,first)
    changed=build_manifest(generator_sha256='b'*64,seed=META_SEED,case_count=12,implementation_commit='commit-a')
    with pytest.raises(RuntimeError):write_manifest(path,changed)
    changed_commit=build_manifest(generator_sha256='a'*64,seed=META_SEED,case_count=12,implementation_commit='commit-b')
    with pytest.raises(RuntimeError):write_manifest(path,changed_commit)
    assert json.loads(path.read_text())==first
