from __future__ import annotations
import json, time
from pathlib import Path
from nexus_gllm.r13x import Proposal, R13XRouter, R13XGovernor, Verifier, Blackboard, R13XEngine

CASES = [
    ("authority_exact", [Proposal("neural","wrong",.99,.01,verification="NEURAL_PROPOSAL"),
                         Proposal("exact","right",.70,.20,verification="EXACT_VERIFIED")], "right"),
    ("abstain_ood", [Proposal("neural","guess",.90,.99,verification="NEURAL_PROPOSAL")], None),
    ("direct_evidence", [Proposal("n","x",.99,.02,verification="NEURAL_PROPOSAL"),
                         Proposal("e","y",.70,.20,evidence=("source",),verification="DIRECT_EVIDENCE")], "y"),
    ("conflict_same_authority", [Proposal("a",True,.8,.1,verification="DIRECT_EVIDENCE"),
                                 Proposal("b",False,.8,.1,verification="DIRECT_EVIDENCE")], None),
]
def main():
    engine=R13XEngine()
    rows=[]
    for name, props, expected in CASES:
        t=time.perf_counter()
        out=engine.answer("benchmark", props)
        ms=(time.perf_counter()-t)*1000
        rows.append({"case":name,"expected":expected,"actual":None if out is None else out.value,
                     "verification":None if out is None else out.verification,"latency_ms":round(ms,4)})
    result={"engine":"R1.3-X","cases":rows,"correct":sum(r["actual"]==r["expected"] for r in rows),
            "total":len(rows)}
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
