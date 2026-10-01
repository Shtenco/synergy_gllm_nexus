from collections import defaultdict
def score(runtime,gold,preds):
    gm={g.case_id:g for g in gold};pm={p.case_id:p for p in preds};n=ok=rep=0;by=defaultdict(lambda:[0,0,0])
    for c in runtime:
        g=gm[c.case_id];p=pm[c.case_id];good=(p.status==g.expected_status and p.truth==g.expected_truth);n+=1;ok+=int(good);rep+=int(p.status=='REPRESENTATION_FAILURE');z=by[c.stratum];z[0]+=1;z[1]+=int(good);z[2]+=int(p.status=='REPRESENTATION_FAILURE')
    return {'n':n,'strict_accuracy':ok/max(1,n),'representation_failure_rate':rep/max(1,n),'by_stratum':{k:{'n':v[0],'strict_accuracy':v[1]/max(1,v[0]),'representation_failure_rate':v[2]/max(1,v[0])} for k,v in sorted(by.items())}}
