from training.v3_hard_oos_d.generator import HardOOSDGenerator

def test_exact_10000_stratum_allocation_and_runtime_quarantine():
    rows=HardOOSDGenerator(404).generate()
    assert len(rows)==10000
    counts={}
    forbidden={'stratum','gold_ast','gold_topology','gold_index','expected_ranking','proof','target_state','counterfactual_gold'}
    for r in rows:
        counts[r.stratum]=counts.get(r.stratum,0)+1
        assert not (set(r.runtime_record()) & forbidden)
    assert counts=={'novel_ast':2000,'partial_noisy':1500,'binding_ambiguity':1500,'temporal_inhibitor':1500,'counterfactual_traps':1500,'mixed_adversarial':2000}
