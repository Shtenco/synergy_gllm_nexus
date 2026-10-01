from benchmarks.crc_m8.run import run_all
def test_ablation_report_has_all_core_organs():
    r=run_all();assert {'program','memory','future','credit','meta'}.issubset(r)
def test_program_ablation_reduces_representation_failure():
    r=run_all()['program'];assert r['crc']['representation_failure_rate']<r['fixed_basis']['representation_failure_rate']
def test_memory_ablation_preserves_raw_provenance():
    r=run_all()['memory'];assert r['hierarchical']['raw_provenance_success']>r['flat_window']['raw_provenance_success']
def test_future_depth_has_nonnegative_gain_on_delayed_reward_suite():
    r=run_all()['future'];assert r['delta_accuracy']>=0
def test_credit_separates_causal_from_spurious():
    r=run_all()['credit'];assert r['causal_minus_spurious_trust']>0
def test_meta_allocates_more_compute_to_hard_case():
    r=run_all()['meta'];assert r['depth_delta']>=0 and r['expert_delta']>=0 and r['memory_delta']>=0
