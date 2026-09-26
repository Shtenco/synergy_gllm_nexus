from __future__ import annotations
import json, random, re
from pathlib import Path
from nexus_gllm.r13x import Proposal,R13XEngine
from nexus_gllm.r13x_trainable import load_checkpoint, generate

OUT=Path("artifacts/r13x_deeptrain"); CKPT=OUT/"r13x_router_deep.pt"
model=load_checkpoint(CKPT)

# Original recovery-branch frozen regression: unchanged 4 cases.
frozen=[
 ("authority_exact",[Proposal("neural","wrong",.99,.01,verification="NEURAL_PROPOSAL"),Proposal("exact","right",.70,.20,verification="EXACT_VERIFIED")],"right"),
 ("abstain_ood",[Proposal("neural","guess",.90,.99,verification="NEURAL_PROPOSAL")],None),
 ("direct_evidence",[Proposal("n","x",.99,.02,verification="NEURAL_PROPOSAL"),Proposal("e","y",.70,.20,evidence=("source",),verification="DIRECT_EVIDENCE")],"y"),
 ("conflict_same_authority",[Proposal("a",True,.8,.1,verification="DIRECT_EVIDENCE"),Proposal("b",False,.8,.1,verification="DIRECT_EVIDENCE")],None)
]
eng=R13XEngine(); frows=[]
for name,props,expected in frozen:
    out=eng.answer(name,props)
    actual=None if out is None else out.value
    frows.append({"case":name,"expected":expected,"actual":actual,"pass":actual==expected})

# Category-matched reconstruction. This is explicitly NOT the lost historical 188-case dataset.
counts={"exact":36,"formal":20,"causal":42,"memory":12,"evidence":18,"semantic":15,"world":15,"language":15,"abstain":15}
assert sum(counts.values())==188
pool=generate(20260929,60)
by={k:[] for k in counts}
for e in pool:
    if e.label in by and len(by[e.label])<counts[e.label]: by[e.label].append(e)
cases=[e for k in counts for e in by[k]]
assert len(cases)==188
rows=[]
for e in cases:
    pred,conf,dist=model.predict(e.text)
    rows.append({"text":e.text,"gold":e.label,"pred":pred,"confidence":conf,"pass":pred==e.label})
# Separate reconstructed open-set 30.
ood=generate(20260930,30)
ood=[e for e in ood if e.label=="abstain"][:30]
orows=[]
for e in ood:
    pred,conf,_=model.predict(e.text); orows.append({"text":e.text,"pred":pred,"confidence":conf,"pass":pred=="abstain"})

result={
 "status":"evaluated",
 "frozen_recovery_regression":{"correct":sum(x["pass"] for x in frows),"total":len(frows),"rows":frows},
 "reconstructed_compound_188":{
   "warning":"Category-matched reconstruction only. Original historical 188 case payload is not recovered and this score must not be reported as a rerun of historical Unified R1.3.",
   "known_historical_reference":"164/188 = 87.23%",
   "counts":counts,
   "correct":sum(x["pass"] for x in rows),"total":188,
   "accuracy":sum(x["pass"] for x in rows)/188,
   "per_category":{k:{"correct":sum(x["pass"] for x in rows if x["gold"]==k),"total":sum(1 for x in rows if x["gold"]==k)} for k in counts}
 },
 "reconstructed_open_set_30":{"correct":sum(x["pass"] for x in orows),"total":len(orows),"rows":orows}
}
(OUT/"posttrain_benchmark.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(result,ensure_ascii=False,indent=2))
