from collections import defaultdict
def score(runtime,gold,preds):
    gm={g.case_id:g for g in gold};pm={p.case_id:p for p in preds};n=len(runtime);strict=exec_ok=plan_ok=mem_ok=trace_ok=0;by=defaultdict(lambda:[0,0])
    for c in runtime:
        g=gm[c.case_id];p=pm[c.case_id]
        e=p.execution_status==g.execution_status and p.execution_truth==g.execution_truth
        pl=p.first_action==g.first_action
        mem=p.memory_count>=g.min_memories
        tr={'meta','memory','program','branch','answer'}.issubset(set(p.trace_kinds))
        ok=e and pl and mem and tr
        strict+=int(ok);exec_ok+=int(e);plan_ok+=int(pl);mem_ok+=int(mem);trace_ok+=int(tr);by[c.stratum][0]+=1;by[c.stratum][1]+=int(ok)
    den=max(1,n)
    return {'n':n,'strict_integrated_accuracy':strict/den,'execution_accuracy':exec_ok/den,'planning_accuracy':plan_ok/den,'memory_retrieval_success':mem_ok/den,'trace_completeness':trace_ok/den,'by_stratum':{k:{'n':v[0],'strict_integrated_accuracy':v[1]/max(1,v[0])} for k,v in sorted(by.items())}}
