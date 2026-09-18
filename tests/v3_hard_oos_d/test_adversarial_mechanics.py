from training.v3_hard_oos_d.generator import HardOOSDGenerator
from training.v3_hard_oos_d.bindings import rename_twin

def test_partial_noisy_ranges_and_ambiguity_unresolved_exist():
    rows=HardOOSDGenerator(405).generate()
    pn=[r for r in rows if r.stratum in {'partial_noisy','mixed_adversarial'}]
    assert all(0.20 <= r.hidden_fraction <= 0.50 for r in pn)
    assert all(0.10 <= r.distractor_fraction <= 0.30 for r in pn)
    assert all(0.0 <= r.noise_fraction <= 0.15 for r in pn)
    amb=[r for r in rows if r.stratum=='binding_ambiguity']
    assert any(r.gold_answer=='UNRESOLVED' for r in amb)

def test_rename_twin_preserves_gold_topology():
    r=HardOOSDGenerator(406).generate(24)[0]
    twin=rename_twin(r)
    assert twin.gold_topology==r.gold_topology
    assert twin.episode_id!=r.episode_id
