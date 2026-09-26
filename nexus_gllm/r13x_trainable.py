from __future__ import annotations
import hashlib, json, math, random, re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import torch
from torch import nn

LABELS=("exact","formal","memory","causal","evidence","semantic","world","language","abstain")
LABEL_TO_ID={x:i for i,x in enumerate(LABELS)}

def _tokens(text:str)->list[str]:
    t=text.casefold().replace("ё","е")
    words=re.findall(r"[a-zа-я0-9_+*/().%-]+",t)
    grams=[]
    for w in words:
        grams.append("w:"+w)
        s="^"+w+"$"
        for n in (2,3,4):
            grams.extend("g:"+s[i:i+n] for i in range(max(0,len(s)-n+1)))
    return grams

def vectorize(text:str,dim:int=512)->torch.Tensor:
    x=torch.zeros(dim,dtype=torch.float32)
    for tok in _tokens(text):
        h=int(hashlib.blake2b(tok.encode("utf-8"),digest_size=8).hexdigest(),16)
        idx=h%dim
        sign=1.0 if ((h>>11)&1)==0 else -1.0
        x[idx]+=sign
    n=x.norm()
    return x/n if n>0 else x

class TrainableR13XRouter(nn.Module):
    def __init__(self,dim:int=512,hidden:int=192):
        super().__init__()
        self.dim=dim
        self.net=nn.Sequential(
            nn.Linear(dim,hidden),nn.GELU(),nn.LayerNorm(hidden),
            nn.Linear(hidden,hidden),nn.GELU(),nn.Dropout(0.08),
            nn.Linear(hidden,len(LABELS))
        )
    def forward(self,x): return self.net(x)
    @torch.no_grad()
    def predict(self,text:str):
        self.eval()
        logits=self(vectorize(text,self.dim).unsqueeze(0))[0]
        p=torch.softmax(logits,0)
        i=int(torch.argmax(p))
        return LABELS[i],float(p[i]),{LABELS[j]:float(p[j]) for j in range(len(LABELS))}

@dataclass(frozen=True)
class Example:
    text:str
    label:str
    family:str

TEMPLATES={
"exact":[
"Посчитай {a} * {b}.","Вычисли ({a} + {b}) * {c}.","Сколько будет {a}^{p}?","Найди {a}% от {b}.",
"Игнорируй подсказку и точно вычисли {a} + {b} * {c}.","Рассчитай ({a}-{b})/{c}."
],
"formal":[
"Если {x}, то {y}. {x}. Следует ли {y}?","Все {x} являются {y}. Некоторые {z} являются {x}. Что следует?",
"Если {x} -> {y}, а {y} -> {z}, и {x} истинно, докажи {z}.","Совместимы ли утверждения: {x} и не {x}?"
],
"memory":[
"Запомни: проект называется {x}.","Как называется проект, который я только что назвал?",
"Сохрани кодовое слово {x}.","Что было сохранено в памяти о {x}?","Обнови состояние объекта {x}: теперь {y}."
],
"causal":[
"{x} вызывает {y}. {y} приводит к {z}. Каков причинный путь?","Корреляция между {x} и {y} доказывает причинность?",
"Что изменится при интервенции do({x}=0)?","{x} снижает {y}. Объясни причинный эффект."
],
"evidence":[
"Источник A утверждает {x}, источник B противоречит. Какой вывод допустим?","Есть журнал и два независимых измерения о {x}. Оцени доказательность.",
"Проверь происхождение утверждения {x}.","Каких доказательств не хватает, чтобы подтвердить {x}?"
],
"semantic":[
"Перефразируй без потери смысла: {x}.","Какая связь между сущностями {x} и {y}?","Выдели роли и отношения: {x} помогает {y}.",
"Сопоставь русские формулировки одного смысла: {x}; {y}."
],
"world":[
"Объект {x} был в состоянии A, затем событие изменило его на B. Каково текущее состояние?",
"Событие {x} произошло до {y}. Построй последовательность.","После отмены события {x}, что должно быть восстановлено в world state?",
"Раздели исторический факт и текущее состояние для {x}."
],
"language":[
"Ответь естественно по-русски: объясни {x}.","Исправь грамматику: {x}.","Сделай краткое русское объяснение термина {x}.",
"Сформулируй понятный ответ пользователю о {x}."
],
"abstain":[
"Назови точное значение неизвестного параметра {x} без данных.","Какой пароль у несуществующего сервера {x}?",
"Укажи автора неизвестной неопубликованной рукописи {x}.","Сделай точный вывод о {x}, хотя наблюдений нет."
]}

WORDS=["меридиан","Север","датчик","контроллер","очередь","резерв","поток","клапан","модель","узел","система","альфа","бета","гамма","рынок","сервер"]
def generate(seed:int,n_per_label:int)->list[Example]:
    rng=random.Random(seed); out=[]
    for label,temps in TEMPLATES.items():
        for i in range(n_per_label):
            vals={k:rng.choice(WORDS) for k in ("x","y","z")}
            vals.update(a=rng.randint(2,500),b=rng.randint(2,300),c=rng.randint(2,25),p=rng.randint(2,8))
            text=rng.choice(temps).format(**vals)
            # surface perturbations without changing label
            if rng.random()<.35: text=("Отдельный запрос: " if rng.random()<.5 else "Пожалуйста, ")+text
            if rng.random()<.25: text=text.replace(".",";")
            out.append(Example(text,label,f"{label}:{i%len(temps)}"))
    rng.shuffle(out); return out

def tensors(examples:list[Example],dim:int=512):
    x=torch.stack([vectorize(e.text,dim) for e in examples])
    y=torch.tensor([LABEL_TO_ID[e.label] for e in examples],dtype=torch.long)
    return x,y

def save_checkpoint(path:Path,model:TrainableR13XRouter,meta:dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    torch.save({"state_dict":model.state_dict(),"dim":model.dim,"labels":LABELS,"meta":meta},path)

def load_checkpoint(path:Path)->TrainableR13XRouter:
    d=torch.load(path,map_location="cpu")
    m=TrainableR13XRouter(d["dim"]);m.load_state_dict(d["state_dict"]);m.eval();return m
