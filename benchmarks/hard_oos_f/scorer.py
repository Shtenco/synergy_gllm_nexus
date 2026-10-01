from collections import defaultdict
def score(runtime,gold,preds):
    gm={g.case_id:g for g in gold};pm={p.case_id:p for p in preds};by=defaultdict(lambda:[0,0,0])
    topology=set();n=correct=status_ok=0
    for c in runtime:
        g=gm[c.case_id];p=pm[c.case_id];n+=1;status_ok+=int(p.status==g.expected_status);ok=p.status==g.expected_status and p.truth==g.expected_truth;correct+=int(ok);by[c.stratum][0]+=1;by[c.stratum][1]+=int(ok);by[c.stratum][2]+=int(p.status=='REPRESENTATION_FAILURE');topology.add(g.topology_sha256)
    return {'n':n,'strict_accuracy':correct/max(1,n),'status_accuracy':status_ok/max(1,n),'representation_failure_rate':sum(v[2] for v in by.values())/max(1,n),'unique_topologies':len(topology),'by_stratum':{k:{'n':v[0],'strict_accuracy':v[1]/max(1,v[0]),'representation_failure_rate':v[2]/max(1,v[0])} for k,v in sorted(by.items())}}
