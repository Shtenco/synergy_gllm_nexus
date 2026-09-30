from __future__ import annotations
from pathlib import Path
import re, zlib
import torch
from torch import nn

PLAN_LABELS=(
"natural_lookup","multihop_compare","multihop_logic","causal_chain",
"memory_read","memory_arith","conflict_latest","world_transition",
"semantic_triple","formal_arith","formal_logic","evidence",
"mixed_memory_compare","abstain"
)

SLOT_TERMS=(
"причин","вызывает","возникает из-за","порождает","эффект","вмешательств","интервен",
"следует","влечет","влечёт","импликац","доказ","логическ","истинно","правило","принадлежит",
"памят","сохран","запис","ячейк","поле","перезапис","сейчас хран","прочита","старое значение","+=",
"сначала","затем","потом","последн","актуальн","текущее","история","по времени",
"состояни","переход","траектори","финальн","после события",
"субъект","агент","действующее лицо","получател","передал","отправил","сообщил","доставил",
"источник","свидетельств","измерен","наблюден","подтвержд","противореч","независим",
"вычисл","посч","результат","арифмет","умнож","прибав","вычесть",
"нет данных","отсутств","неизвест","не фантаз","выдумк","нет сведений","невозможно",
"сравни","что больше","какое поле","переменная больше","после обновления"
)

CHAR_DIM=2048
WORD_DIM=1792
FEATURE_DIM=4096

def features(text:str)->torch.Tensor:
    t=text.casefold().replace("ё","е")
    words=re.findall(r"[a-zа-я0-9_]+|=>|->|[+=*/()><:-]",t)
    x=torch.zeros(FEATURE_DIM,dtype=torch.float32)
    for w in words:
        toks=["w:"+w]; s="^"+w+"$"
        for n in (2,3,4):
            toks.extend(f"g{n}:"+s[i:i+n] for i in range(max(0,len(s)-n+1)))
        for tok in toks:
            h=zlib.crc32(tok.encode("utf-8"))
            x[h%CHAR_DIM]+=1.0 if (h&1)==0 else -1.0
    for n in (2,3):
        for i in range(max(0,len(words)-n+1)):
            tok=f"{n}:"+"|".join(words[i:i+n])
            h=zlib.crc32(tok.encode("utf-8"))
            x[CHAR_DIM+(h%WORD_DIM)]+=1.0 if (h&1)==0 else -1.0
    base=CHAR_DIM+WORD_DIM
    for i,term in enumerate(SLOT_TERMS):
        if base+i>=FEATURE_DIM: break
        if term in t:x[base+i]=1.0
    norm=x.norm()
    return x/norm if norm>0 else x

class ResidualBlock(nn.Module):
    def __init__(self,h:int=768,drop:float=.08):
        super().__init__()
        self.n1=nn.LayerNorm(h); self.l1=nn.Linear(h,h)
        self.n2=nn.LayerNorm(h); self.l2=nn.Linear(h,h)
        self.drop=nn.Dropout(drop)
    def forward(self,x):
        y=torch.nn.functional.gelu(self.l1(self.n1(x)))
        y=self.drop(y)
        y=torch.nn.functional.gelu(self.l2(self.n2(y)))
        return x+y

class UnifiedRUPlannerV2(nn.Module):
    def __init__(self,dim:int=FEATURE_DIM,h:int=768,blocks:int=2):
        super().__init__()
        self.inp=nn.Sequential(nn.Linear(dim,h),nn.GELU(),nn.LayerNorm(h))
        self.blocks=nn.Sequential(*[ResidualBlock(h) for _ in range(blocks)])
        self.head=nn.Sequential(nn.Linear(h,384),nn.GELU(),nn.LayerNorm(384),nn.Linear(384,len(PLAN_LABELS)))
    def forward(self,x): return self.head(self.blocks(self.inp(x)))
    @torch.no_grad()
    def predict(self,text:str):
        self.eval(); p=torch.softmax(self(features(text).unsqueeze(0))[0],0)
        i=int(p.argmax())
        return PLAN_LABELS[i],float(p[i]),{PLAN_LABELS[j]:float(p[j]) for j in range(len(PLAN_LABELS))}

def load_planner(path:str|Path)->UnifiedRUPlannerV2:
    d=torch.load(Path(path),map_location="cpu")
    m=UnifiedRUPlannerV2()
    m.load_state_dict(d["state_dict"]);m.eval()
    return m
