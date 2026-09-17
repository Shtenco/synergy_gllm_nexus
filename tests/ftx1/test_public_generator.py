from benchmarks.ftx1.public_generator import TRACKS, generate_dev, generate_shadow


def flatten(bundle):
    return [p for track in TRACKS for p in bundle[track]]


def test_dev_shadow_are_deterministic_complete_and_disjoint():
    dev1 = generate_dev(11017)
    dev2 = generate_dev(11017)
    shadow = generate_shadow(22017)
    assert dev1 == dev2
    assert set(dev1) == set(TRACKS) == set(shadow)
    assert all(len(dev1[t]) >= 8 for t in TRACKS)
    assert all(len(shadow[t]) >= 8 for t in TRACKS)
    dev_ids = {c.case_id for c,_ in flatten(dev1)}
    sh_ids = {c.case_id for c,_ in flatten(shadow)}
    assert dev_ids.isdisjoint(sh_ids)
    dev_ns = {g.audit_dict()['ontology_ns'] for _,g in flatten(dev1)}
    sh_ns = {g.audit_dict()['ontology_ns'] for _,g in flatten(shadow)}
    assert dev_ns.isdisjoint(sh_ns)


def test_public_runtime_payload_never_exposes_audit_metadata():
    for bundle in (generate_dev(1), generate_shadow(2)):
        for case,_ in flatten(bundle):
            assert set(case.to_runtime_dict()) == {'case_id','prompt','history','documents'}
