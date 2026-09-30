from __future__ import annotations
import json, random
from pathlib import Path
import torch
from torch import nn

from nexus_gllm.r13x_trainable import LABELS, LABEL_TO_ID, TrainableR13XRouter, vectorize

WORDS=["меридиан","Север","датчик","контроллер","очередь","резерв","поток","клапан","модель","узел","система","альфа","бета","гамма","рынок","сервер","агент","память","состояние","граф"]

TRAIN={
"exact":["Вычисли {a} * {b}.","Чему равно ({a}+{b})*{c}?","Найди остаток от деления {a} на {c}.","Рассчитай произведение чисел {a} и {b}."],
"formal":["Если {x}, то {y}. {x}. Следует ли {y}?","Если {x} -> {y}, а {y} -> {z}, и {x} истинно, докажи {z}.","Проверь, выводится ли {y} из условия {x}."],
"memory":["Запомни: режим = {x}.","Какое значение режима я сохранил?","Перезапиши память: поле {x} теперь равно {y}."],
"causal":["{x} вызывает {y}. {y} приводит к {z}. Каков причинный путь?","Что изменится при интервенции do({x}=0)?","Отличи причинную связь {x}->{y} от корреляции."],
"evidence":["Источник A утверждает {x}, источник B противоречит. Какой вывод допустим?","Каких доказательств не хватает для {x}?","Отдели наблюдаемое доказательство от предположения о {x}."],
"semantic":["Выдели субъект, отношение и объект: {x} помогает {y}.","Какая семантическая связь между {x} и {y}?","Извлеки смысловые роли из предложения о {x} и {y}."],
"world":["{x} был A, затем стал B. Каково текущее состояние?","Событие {x} произошло до {y}. Построй timeline.","После переходов A->B->C для {x} назови текущее состояние."],
"language":["Ответь естественно по-русски: объясни {x}.","Перепиши фразу литературно и понятно: {x}.","Сделай фразу про {x} естественной и грамотной."],
"abstain":["Назови точное значение закрытого параметра {x}, хотя данных нет.","Ответь без выдумки, если сведений о {x} нет.","Данных о {x} недостаточно: можно ли назвать точное значение?"]}

OOS={
"exact":["Реши без догадок: {a} умножить на {b}, затем вычесть {c}.","Сколько получится при целочисленном делении {a} на {c}?"],
"formal":["Из A следует B, из B следует C. A верно. Обязано ли быть верно C?","Проверь логическое следование без добавления новых посылок: {x} => {y}."],
"memory":["Я раньше попросил сохранить метку {x}. Верни именно сохраненную метку.","Замени прежнее значение поля {x} новым значением {y} и запомни."],
"causal":["Если принудительно отключить {x}, как это повлияет на {y} по заданной причинной цепи?","Отличи причинный эффект от простой совместной изменчивости {x} и {y}."],
"evidence":["Есть два независимых свидетельства о {x}; оцени, достаточно ли их для утверждения.","Отдели факт, источник и неподтвержденный вывод для {x}."],
"semantic":["Кто действует, что делает и на кого направлено действие: {x} передает данные {y}.","Нормализуй смысловую тройку из русского предложения про {x} и {y}."],
"world":["Какое состояние актуально сейчас, если {x} сначала был A, потом B, потом C?","Отличи историческое состояние {x} от текущего."],
"language":["Сделай ответ по-русски естественным, без канцелярита, про {x}.","Исправь грамматику и сохрани смысл фразы про {x}."],
"abstain":["Можно ли назвать точный факт о {x}, если исходных данных вообще нет?","Не выдумывай: что ответить на запрос о неизвестном значении {x}?"]}

def generate(bank,n,seed):
    r=random.Random(seed); rows=[]
    for label,temps in bank.items():
        for _ in range(n):
            vals={k:r.choice(WORDS) for k in ("x","y","z")}
            vals.update(a=r.randint(2,700),b=r.randint(2,500),c=r.randint(2,30))
            text=r.choice(temps).format(**vals)
            if r.random()<.4:text=r.choice(["Пожалуйста, ","Отдельный запрос: ","Без лишних слов: ",""])+text
            rows.append((text,LABEL_TO_ID[label]))
    r.shuffle(rows); return rows

def tensors(rows,dim=512):
    return torch.stack([vectorize(t,dim) for t,_ in rows]),torch.tensor([y for _,y in rows])

def main(out_dir="artifacts/unified_russian_cognitive_runtime_v1"):
    train=generate(TRAIN,500,17); val=generate(TRAIN,100,23); oos=generate(OOS,120,31)
    X,Y=tensors(train); VX,VY=tensors(val); OX,OY=tensors(oos)
    torch.manual_seed(7); m=TrainableR13XRouter(dim=512); opt=torch.optim.AdamW(m.parameters(),lr=2e-3,weight_decay=1e-3); lossf=nn.CrossEntropyLoss()
    best=None
    for ep in range(30):
        m.train(); perm=torch.randperm(len(X))
        for i in range(0,len(X),128):
            ix=perm[i:i+128]; opt.zero_grad(); loss=lossf(m(X[ix]),Y[ix]); loss.backward(); opt.step()
        m.eval()
        with torch.no_grad():
            va=(m(VX).argmax(1)==VY).float().mean().item(); oa=(m(OX).argmax(1)==OY).float().mean().item()
        score=(va+oa)/2
        if best is None or score>best[0]:
            best=(score,ep,va,oa,{k:v.detach().cpu().clone() for k,v in m.state_dict().items()})
    m.load_state_dict(best[4]); out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    meta={"seed":7,"train_examples":len(train),"val_examples":len(val),"oos_examples":len(oos),"best_epoch":best[1],"val_accuracy":best[2],"oos_accuracy":best[3],"labels":LABELS,"status":"BASELINE_TRAINED_NOT_FINAL"}
    torch.save({"state_dict":m.state_dict(),"dim":512,"labels":LABELS,"meta":meta},out/"ru_router_v1.pt")
    (out/"ROUTER_TRAINING_METRICS.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
