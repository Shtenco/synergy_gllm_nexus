from training.v3_hard_oos_d.scorer import score_records

def test_representation_failures_stay_in_denominator_and_all_strata_report():
    rows=[]
    strata=['novel_ast','partial_noisy','binding_ambiguity','temporal_inhibitor','counterfactual_traps','mixed_adversarial']
    for s in strata:
        rows.append({'stratum':s,'correct':False,'representation_failure':True,'confidence':0.9,'gold_positive':True})
        rows.append({'stratum':s,'correct':True,'representation_failure':False,'confidence':0.8,'gold_positive':True})
    m=score_records(rows)
    assert m['answer_accuracy']==0.5
    assert m['representation_failure_rate']==0.5
    assert set(m['by_stratum'])==set(strata)
