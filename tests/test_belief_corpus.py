from training.generate_belief_corpus import generate_records, build_manifest


def test_default_stage_a_has_exact_sizes_and_train_distribution():
    rows = generate_records(seed=17)
    manifest = build_manifest(rows, seed=17)
    assert manifest["counts"] == {"train": 100000, "dev": 10000, "blind": 10000}
    assert manifest["task_counts"]["train"] == {
        "ordinary_relation": 20000,
        "contradictory_evidence": 15000,
        "source_reliability": 10000,
        "temporal_revision": 10000,
        "causal_evidence": 10000,
        "multi_source_agreement": 10000,
        "continual_memory_retention": 10000,
        "misinformation_correction": 5000,
        "abstention_unknown": 5000,
        "protected_facts_rollback": 5000,
    }
    assert len(rows) == 120000


def test_split_templates_sources_and_entities_are_disjoint():
    rows = generate_records(seed=17, train_total=1000, dev_total=100, blind_total=100)
    by_split = {name: [r for r in rows if r["split"] == name] for name in ("train", "dev", "blind")}
    template_sets = {name: {r["template_id"] for r in values} for name, values in by_split.items()}
    source_prefixes = {name: {r["observations"][0]["source"].split("-")[0] for r in values} for name, values in by_split.items()}
    entity_prefixes = {name: {r["subject"].split("_")[0] for r in values} for name, values in by_split.items()}
    assert template_sets["train"].isdisjoint(template_sets["dev"])
    assert template_sets["train"].isdisjoint(template_sets["blind"])
    assert template_sets["dev"].isdisjoint(template_sets["blind"])
    assert source_prefixes == {"train": {"trsrc"}, "dev": {"devsrc"}, "blind": {"blsrc"}}
    assert entity_prefixes == {"train": {"tr"}, "dev": {"dev"}, "blind": {"bl"}}


def test_fixed_seed_manifest_sha_is_deterministic():
    a = generate_records(seed=123, train_total=100, dev_total=20, blind_total=20)
    b = generate_records(seed=123, train_total=100, dev_total=20, blind_total=20)
    assert build_manifest(a, seed=123)["sha256"] == build_manifest(b, seed=123)["sha256"]
