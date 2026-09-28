from __future__ import annotations
import argparse, hashlib, json, random, re
from pathlib import Path
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

CATS=("natural_ru","multi_hop","causal","memory_context","conflicting_memory","world_state","semantic_graph","formal_executable","evidence_epistemic","mixed_cognitive")
C2I={x:i for i,x in enumerate(CATS)}
NAMES=("Анна","Борис","Вера","Глеб","Дина","Егор","Жанна","Илья","Кира","Лев")
OBJ=("датчик","контроллер","сервер","модуль","канал","буфер","агент","процесс")
VAL=("меридиан","кварц","север","омега","дельта","маяк","вектор","спектр")
COL=("красный","синий","зелёный","жёлтый","белый","чёрный","серый","фиолетовый")
STATE=("ожидание","активен","пауза","ошибка","готов","закрыт","открыт","архив")

def norm(x): return str(x).casefold().replace("ё","е").strip(" .,:;!?\n\t")
def pick(r,p,n): return r.sample(list(p),n)
def row(cat,r,oos=False):
    if cat=="natural_ru":
        v,w=pick(r,VAL,2); t=(f"Хотя в архиве встречается {w}, действующая метка проекта — {v}. Какова она?" if oos else f"Метка проекта — {v}. Назови её."); return t,v
    if cat=="multi_hop":
        a,b,c=pick(r,NAMES,3); t=(f"Сначала сказано, что {b} сильнее {c}; дополнительно {a} сильнее {b}. Кто сильнее всех?" if oos else f"{a} старше {b}; {b} старше {c}. Кто старше всех?"); return t,a
    if cat=="causal":
        a,b,c=pick(r,OBJ,3); t=(f"Если {a} обусловливает {b}, а эффект {b} проявляется как {c}, назови конечное следствие." if oos else f"{a} запускает {b}, а {b} вызывает {c}. Что в конце цепочки?"); return t,c
    if cat=="memory_context":
        v,w=pick(r,VAL,2); t=(f"Историческая заметка: {w}. Актуальная запись поля равна {v}. Что вернуть сейчас?" if oos else f"Поле хранит {v}. Что хранится в поле?"); return t,v
    if cat=="conflicting_memory":
        a,b=pick(r,COL,2); t=(f"Раньше использовался {a}, но последняя фиксация даёт {b}. Какой цвет актуален?" if oos else f"Сначала цвет был {a}, позже его изменили на {b}. Какой цвет сейчас?"); return t,b
    if cat=="world_state":
        a,b,c=pick(r,STATE,3); t=(f"На раннем этапе было {a}, впоследствии {b}, а к моменту запроса состояние {c}. Что актуально?" if oos else f"Состояния: {a} → {b} → {c}. Что сейчас?"); return t,c
    if cat=="semantic_graph":
        a,b=pick(r,NAMES,2); t=(f"Получателем был {b}; документ к нему направил {a}. Кто субъект действия?" if oos else f"{a} передал документ {b}. Кто отправитель?"); return t,a
    if cat=="formal_executable":
        a=r.randint(10,90); b=r.randint(2,19); op=r.choice(("+","-","*")); ans=str(a+b if op=="+" else a-b if op=="-" else a*b); t=(f"Без оценки найди результат {a} {op} {b}." if oos else f"Вычисли {a} {op} {b}."); return t,ans
    if cat=="evidence_epistemic":
        if r.random()<.5: return ("Два независимых наблюдения согласованно подтверждают факт, противоречий нет. Каков статус?" if oos else "Два независимых источника подтверждают факт. Каков статус?"),"подтверждено"
        return ("Нет ни измерений, ни независимых свидетельств. Каков допустимый вывод?" if oos else "Нет данных и источников. Каков статус?"),"недостаточно данных"
    a=r.randint(5,50); b=r.randint(5,50); d=r.randint(1,20); aa=a+d; ans="A" if aa>b else "B" if b>aa else "равны"; t=(f"Изначально B={b}, A={a}; только к A прибавляют {d}. Что больше?" if oos else f"A={a}, B={b}; затем A увеличивают на {d}. Что больше?"); return t,ans

def gen(seed,n,oos=False):
    r=random.Random(seed); out=[]
    for c in CATS:
        for _ in range(n):
            t,a=row(c,r,oos); out.append({"text":t,"category":c,"answer":a})
    r.shuffle(out); return out

def hrows(rows):
    raw="\n".join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")) for x in rows).encode(); return hashlib.sha256(raw).hexdigest()

def solve_symbolic(t,c):
    nums=[int(x) for x in re.findall(r"\b\d+\b",t)]
    if c=="formal_executable" and len(nums)>=2:
        if "*" in t:return str(nums[0]*nums[1])
        if "+" in t:return str(nums[0]+nums[1])
        if "-" in t:return str(nums[0]-nums[1])
    if c=="evidence_epistemic": return "недостаточно данных" if "нет " in norm(t) else "подтверждено"
    if c=="mixed_cognitive" and len(nums)>=3:
        ma=re.search(r"A=(\d+)",t); mb=re.search(r"B=(\d+)",t); d=nums[-1]
        if ma and mb:
            a=int(ma.group(1))+d; b=int(mb.group(1)); return "A" if a>b else "B" if b>a else "равны"
    return None

class DS(Dataset):
    def __init__(self,r): self.r=r
    def __len__(self): return len(self.r)
    def __getitem__(self,i): return self.r[i]

class Adapter(nn.Module):
    def __init__(self,h):
        super().__init__(); d=384; self.proj=nn.Linear(h,d); layer=nn.TransformerEncoderLayer(d,6,1536,.08,batch_first=True,norm_first=True,activation="gelu"); self.ctx=nn.TransformerEncoder(layer,2); self.norm=nn.LayerNorm(d); self.plan=nn.Linear(d,len(CATS)); self.ptr=nn.Linear(d,2)
    def forward(self,h,mask):
        x=self.norm(self.ctx(self.proj(h),src_key_padding_mask=~mask.bool())); w=mask.unsqueeze(-1).float(); p=(x*w).sum(1)/w.sum(1).clamp_min(1.0); return self.plan(p),self.ptr(x)

def train(args):
    from transformers import AutoModel, AutoTokenizer
    torch.manual_seed(args.seed); random.seed(args.seed); torch.set_num_threads(args.threads)
    tr=gen(args.seed,args.train_per_cat,False); va=gen(args.seed+1,args.val_per_cat,False); k=gen(args.k_seed,args.k_per_cat,True); kh=hrows(k)
    if args.expected_k_sha and kh!=args.expected_k_sha: raise SystemExit(f"K SHA mismatch {kh}")
    tok=AutoTokenizer.from_pretrained(args.model,use_fast=True); base=AutoModel.from_pretrained(args.model,torch_dtype=torch.float32,low_cpu_mem_usage=True); base.eval(); [p.requires_grad_(False) for p in base.parameters()]
    ad=Adapter(base.config.hidden_size); opt=torch.optim.AdamW(ad.parameters(),lr=args.lr); ce=nn.CrossEntropyLoss(); pce=nn.CrossEntropyLoss(ignore_index=-100,weight=torch.tensor([1.0,8.0]))
    def collate(batch):
        texts=[x["text"] for x in batch]; e=tok(texts,padding=True,truncation=True,max_length=96,return_tensors="pt",return_offsets_mapping=True); off=e.pop("offset_mapping"); y=torch.tensor([C2I[x["category"]] for x in batch]); ptr=torch.full(e["input_ids"].shape,-100,dtype=torch.long)
        for i,x in enumerate(batch):
            ans=norm(x["answer"]); found=False
            for j,(s,z) in enumerate(off[i].tolist()):
                if z<=s: continue
                ptr[i,j]=0; piece=norm(x["text"][s:z])
                if ans and (piece==ans or ans.startswith(piece) or piece.startswith(ans)): ptr[i,j]=1; found=True
            if x["category"] in ("formal_executable","evidence_epistemic","mixed_cognitive") or not found: ptr[i,:]=-100
        return e,y,ptr,batch,off
    def ev(rows,final=False):
        dl=DataLoader(DS(rows),batch_size=args.batch,collate_fn=collate); ad.eval(); pc=n=apc=apn=fc=fn=0
        with torch.no_grad():
            for e,y,ptr,batch,off in dl:
                h=base(input_ids=e["input_ids"],attention_mask=e["attention_mask"]).last_hidden_state; po,ao=ad(h,e["attention_mask"]); pp=po.argmax(-1); pc+=int((pp==y).sum()); n+=len(y); prob=torch.softmax(ao,-1)[...,1]
                for i,x in enumerate(batch):
                    valid=(ptr[i]>=0); pred=""
                    if valid.any():
                        idx=int(torch.where(valid,prob[i],torch.tensor(-1.)).argmax()); s,z=off[i,idx].tolist(); left,right=s,z
                        while left>0 and re.match(r"[A-Za-zА-Яа-яЁё0-9_]",x["text"][left-1]): left-=1
                        while right<len(x["text"]) and re.match(r"[A-Za-zА-Яа-яЁё0-9_]",x["text"][right]): right+=1
                        pred=x["text"][left:right]; apn+=1; apc+=int(norm(pred)==norm(x["answer"]))
                    if final:
                        cat=CATS[int(pp[i])]; out=solve_symbolic(x["text"],cat) if cat in ("formal_executable","evidence_epistemic","mixed_cognitive") else pred; fn+=1; fc+=int(cat==x["category"] and norm(out or "")==norm(x["answer"]))
        return {"plan_accuracy":pc/n,"answer_pointer_accuracy":apc/max(1,apn),"final_answer_accuracy":fc/max(1,fn) if final else None,"items":n}
    best=None; dl=DataLoader(DS(tr),batch_size=args.batch,shuffle=True,collate_fn=collate)
    for ep in range(1,args.epochs+1):
        ad.train(); total=0
        for e,y,ptr,batch,off in dl:
            with torch.no_grad(): h=base(input_ids=e["input_ids"],attention_mask=e["attention_mask"]).last_hidden_state
            po,ao=ad(h,e["attention_mask"]); loss=ce(po,y); valid=(ptr.view(-1)>=0)
            if valid.any(): loss=loss+.6*pce(ao.view(-1,2),ptr.view(-1))
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(ad.parameters(),1.0); opt.step(); total+=float(loss)
        m=ev(va,False); print(json.dumps({"epoch":ep,"loss":total/max(1,len(dl)),"validation":m},ensure_ascii=False),flush=True); score=m["plan_accuracy"]+m["answer_pointer_accuracy"]
        if best is None or score>best[0]: best=(score,{k:v.detach().cpu().clone() for k,v in ad.state_dict().items()},m,ep)
    ad.load_state_dict(best[1]); km=ev(k,True); out=Path(args.out); out.mkdir(parents=True,exist_ok=True); torch.save({"state_dict":ad.state_dict(),"model":args.model,"k_sha":kh,"validation":best[2],"hard_oos_k":km},out/"nexus_v8_qwen3_06b_adapter.pt"); sha=hashlib.sha256((out/"nexus_v8_qwen3_06b_adapter.pt").read_bytes()).hexdigest(); meta={"backbone":args.model,"backbone_parameters":sum(p.numel() for p in base.parameters()),"trainable_parameters":sum(p.numel() for p in ad.parameters()),"train_examples":len(tr),"validation_examples":len(va),"hard_oos_k_examples":len(k),"hard_oos_k_sha256":kh,"validation":best[2],"hard_oos_k":km,"adapter_sha256":sha,"best_epoch":best[3]}; (out/"METRICS.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)); print(json.dumps(meta,ensure_ascii=False,indent=2),flush=True)

def main():
    p=argparse.ArgumentParser(); p.add_argument("--seal-only",action="store_true"); p.add_argument("--model",default="Qwen/Qwen3-0.6B"); p.add_argument("--seed",type=int,default=2026092814); p.add_argument("--k-seed",type=int,default=2026092816); p.add_argument("--train-per-cat",type=int,default=300); p.add_argument("--val-per-cat",type=int,default=70); p.add_argument("--k-per-cat",type=int,default=120); p.add_argument("--batch",type=int,default=6); p.add_argument("--epochs",type=int,default=2); p.add_argument("--threads",type=int,default=4); p.add_argument("--lr",type=float,default=8e-4); p.add_argument("--expected-k-sha",default=""); p.add_argument("--out",default="artifacts/unified_russian_cognitive_runtime_v8_proxy"); a=p.parse_args(); k=gen(a.k_seed,a.k_per_cat,True); print(json.dumps({"items":len(k),"sha256":hrows(k),"seed":a.k_seed},ensure_ascii=False,indent=2)) if a.seal_only else train(a)
if __name__=="__main__": main()
