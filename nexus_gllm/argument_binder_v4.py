from __future__ import annotations
import re
from .cognitive_ir_v4 import CognitiveIR
from .compositional_cognitive_executor_v2 import _norm, NAMES, OBJECTS, COLORS, STATES, VALUES

NOISE_MARKERS=(
"не участвует","не связан","не учитывай","игнорируй","посторонн","лишн","шум",
"не путай","ничего не известно","не относится","не входит в действие","не считай",
"не трогай","упомянут отдельно","относится к другому","другой счётчик",
"другое поле","другой объект","служебн","нерелевант","чужой"
)

def _mentions(text,vocab):
    t=_norm(text); out=[]
    for v in vocab:
        nv=_norm(v); pos=0
        while True:
            p=t.find(nv,pos)
            if p<0:break
            out.append((p,v));pos=p+len(nv)
    return tuple(v for _,v in sorted(out))

def _strip_noise(text):
    parts=re.split(r"(?<=[.!?])\s+",text); kept=[]; dropped=[]
    for p in parts:
        pn=_norm(p)
        if any(m in pn for m in NOISE_MARKERS):
            dropped.append(p)
            if ":" in p:
                suffix=p.split(":",1)[1].strip()
                if suffix:kept.append(suffix)
            elif ";" in p:
                suffix=p.split(";",1)[1].strip()
                if suffix:kept.append(suffix)
            continue
        kept.append(p)
    return " ".join(kept).strip(),tuple(dropped)

class ArgumentBinderV4:
    def bind(self,text:str,plan:str)->CognitiveIR:
        clean,dropped=_strip_noise(text)
        low=_norm(clean)
        nums=tuple(int(x) for x in re.findall(r"\b\d+\b",clean))
        relevant=[]
        if plan in ("multihop_compare","semantic_triple"):
            relevant=list(_mentions(clean,NAMES))
        elif plan in ("multihop_logic","causal_chain"):
            relevant=list(_mentions(clean,OBJECTS))
        elif plan=="conflict_latest":
            relevant=list(_mentions(clean,COLORS))
        elif plan=="world_transition":
            relevant=list(_mentions(clean,STATES))
        elif plan in ("natural_lookup","memory_read"):
            relevant=list(_mentions(clean,VALUES+COLORS+STATES))
        subject=relevant[0] if relevant else None
        obj=relevant[-1] if relevant else None
        return CognitiveIR(plan=plan,subject=subject,object=obj,operands=nums,
                           timeline=tuple(relevant),relevant=tuple(relevant),
                           distractors=dropped,metadata={"clean_text":clean})
