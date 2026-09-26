from __future__ import annotations
import hashlib,re
from pathlib import Path
import torch
from torch import nn

LABELS=("exact","formal","memory","causal","evidence","semantic","world","language","abstain")
HASH_DIM=192

LEX={
"exact":["вычис","посчит","арифмет","числен","умнож","раздел","остат","процент","математ","compute","evaluate","numeric","remainder","multiply","plus","minus","делен"],
"formal":["если","следу","посыл","логич","доказ","противореч","имплика","entail","premise","formal","modus","истинн","заключен"],
"memory":["запом","сохрани","памят","ранее","запис","напом","remember","retrieve","stored","код","метк","профил"],
"causal":["причин","вызыва","влия","intervention","intervene","do(","корреля","downstream","effect","cause","фактор","цепочк","медиат"],
"evidence":["источник","свидетел","evidence","provenance","журнал","измерен","подтверд","claim","первич","доказатель","corrobor","аудит"],
"semantic":["смысл","сущност","отношен","роль","agent","subject","object","relation","paraphrase","кто что","семантич","thematic","тройк"],
"world":["состояни","событи","текущ","истор","snapshot","timeline","rollback","world state","t1","t2","статус","временн","последовательн"],
"language":["русск","стиль","граммат","переформулир","переведи","fluent","понятн","сократи","объясни","rewrite","формулировк","литератур"],
"abstain":["нет данных","без данных","нет наблюден","неизвест","анонимн","без источ","недостат","невозможно","no evidence","unknown","hidden","нет лог","выдум"],
}
CONCEPTS=[(lab,t) for lab,terms in LEX.items() for t in terms]
FEATURE_DIM=HASH_DIM+len(CONCEPTS)+12

def features(text:str)->torch.Tensor:
    t=text.casefold().replace("ё","е")
    x=torch.zeros(FEATURE_DIM,dtype=torch.float32)
    for w in re.findall(r"[a-zа-я0-9_+*/().%=>:-]+",t):
        toks=["w:"+w]; s="^"+w+"$"
        for n in (2,3):
            toks.extend("g:"+s[i:i+n] for i in range(max(0,len(s)-n+1)))
        for tok in toks:
            h=int(hashlib.blake2b(tok.encode("utf-8"),digest_size=8).hexdigest(),16)
            x[h%HASH_DIM]+=1.0 if ((h>>11)&1)==0 else -1.0
    off=HASH_DIM
    for i,(_,term) in enumerate(CONCEPTS):
        x[off+i]=1.0 if term in t else 0.0
    off+=len(CONCEPTS)
    x[off+0]=sum(ch.isdigit() for ch in t)/max(1,len(t))
    x[off+1]=1.0 if re.search(r"\d\s*[*+/%^-]\s*\d",t) else 0.0
    x[off+2]=1.0 if "->" in t or "=>" in t or "→" in t else 0.0
    x[off+3]=1.0 if "?" in text else 0.0
    x[off+4]=1.0 if re.search(r"\b(if|если)\b",t) else 0.0
    x[off+5]=1.0 if "do(" in t else 0.0
    x[off+6]=1.0 if any(q in t for q in ("кто","какой","какая","what","who")) else 0.0
    x[off+7]=1.0 if any(q in t for q in ("без","нет","no ","unknown")) else 0.0
    x[off+8]=min(1.0,len(t)/180.0)
    x[off+9]=1.0 if any(q in t for q in ("t1","t2","snapshot","timeline")) else 0.0
    x[off+10]=1.0 if any(q in t for q in ("source","источник","evidence","provenance")) else 0.0
    x[off+11]=1.0 if any(q in t for q in ("remember","запом","памят","сохрани")) else 0.0
    n=x[:HASH_DIM].norm()
    if n>0: x[:HASH_DIM]/=n
    return x

class SemanticRouter(nn.Module):
    def __init__(self):
        super().__init__()
        self.net=nn.Sequential(nn.Linear(FEATURE_DIM,128),nn.GELU(),nn.LayerNorm(128),
                               nn.Linear(128,96),nn.GELU(),nn.Linear(96,len(LABELS)))
    def forward(self,x): return self.net(x)

def high_precision_gate(text:str):
    t=text.casefold().replace("ё","е")
    noev=any(q in t for q in ("нет данных","данных нет","нет наблюден","наблюдений нет","без измерен","нет измерен","метаданн","metadata отсутств","no evidence","no measurements","информация отсутств","полностью отсутств","без источника","без логов"))
    demand=any(q in t for q in ("точн","достоверн","гарантирован","exact","reliable","назови","укажи","установ"))
    if noev and demand: return "abstain"
    if re.search(r"\d\s*[×*+/^-]\s*\(?\d",t) or any(q in t for q in ("произведен","сумма","разност","modulo","остаток","процент","квадрат","squared","арифмет","числен","вычис","посчит","делени")): return "exact"
    if any(q in t for q in ("причин","вызыва","interven","вмешатель","do(","корреляц","downstream","confound","cause"," effect","устранить причину","каузал")): return "causal"
    if any(q in t for q in ("запом","сохрани","запиши","ранее","предыдущ","памят","remember","retrieve","сохранен","сохранён","верни позже","кодовое слово","занеси")): return "memory"
    if any(q in t for q in ("snapshot","timeline","world state","состояни","событи","историческ","текущ","актуальн","rollback","t0","t1","t2","state transition","event log","active state")): return "world"
    if any(q in t for q in ("если ","посылк","entail","следует ли","логически следует","обязательно ли","доказуем","доказать","докажи","противореч","несовмест","имплика","premises","формальн","принадлежит")) or "→" in t: return "formal"
    if any(q in t for q in ("источник","evidence","provenance","подтвержд","свидетел","первичн","измерен","claim","corrobor","доказательств","аудит происхождения","протокол","сенсор","журнал")): return "evidence"
    if any(q in t for q in ("агент","субъект","объект","получател","семантическ","semantic role","semantic relation","subject-relation-object","сущност","отношени","смысл","парафраз","paraphrase","кто что сделал","entity-relation","relation triple")): return "semantic"
    if any(q in t for q in ("по-русски","русском","граммат","стил","перепиши","rewrite","fluent russian","сократи","простыми словами","переведи","формулировк","редакт")): return "language"
    return None

class HybridR13XRouter:
    def __init__(self,checkpoint:Path):
        d=torch.load(checkpoint,map_location="cpu")
        self.model=SemanticRouter(); self.model.load_state_dict(d["state_dict"]); self.model.eval()
    @torch.no_grad()
    def route(self,text:str):
        gate=high_precision_gate(text)
        if gate is not None: return gate,1.0,"authority_gate"
        p=torch.softmax(self.model(features(text).unsqueeze(0))[0],0)
        i=int(p.argmax()); return LABELS[i],float(p[i]),"learned"
