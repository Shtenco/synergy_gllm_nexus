def score(cases,preds):
    pm={p.case_id:p for p in preds};correct=prov=0
    for c in cases:
        p=pm[c.case_id];correct+=int(p.value==c.gold_value);prov+=int(p.raw_evidence_count>=c.gold_min_raw)
    n=max(1,len(cases));return {'n':len(cases),'current_value_accuracy':correct/n,'raw_provenance_success':prov/n}
