from __future__ import annotations
import json, tempfile
from pathlib import Path
from nexus_gllm.r13x_cognitive_ru import CognitiveRussianRuntime

DIALOGUES=[
{"name":"identity3","turns":[
 ["Добрый вечер! Представься.",["nexus"]],
 ["Что ты умеешь делать с состояниями и памятью?",["состояни","памят"]]
]},
{"name":"memory3","turns":[
 ["Сохрани — имя модели = Орбита.",["имя модели","орбита"]],
 ["Что было сохранено про имя модели?",["орбита"]],
 ["Что я сказал раньше?",["имя модели","орбита"]]
]},
{"name":"world3","turns":[
 ["Состояние документа теперь согласовано.",["документ","согласован"]],
 ["Теперь документ опубликован, обнови его состояние.",["опубликован"]],
 ["Каково состояние документа?",["опубликован"]]
]},
{"name":"relation3","turns":[
 ["Письмо Олегу дала Ирина.",["ирин","олег","письм"]],
 ["Кто дал письмо Олегу?",["ирин"]]
]},
{"name":"math3","turns":[
 ["Рассчитай (7 + 5) * 6.",["72"]],
 ["Сколько 9 умножить на 11?",["99"]],
 ["Чему равно 100 разделить на 4?",["25"]]
]},
{"name":"formal3","turns":[
 ["Если аккумулятор разряжен, устройство выключается. аккумулятор разряжен. Что следует?",["устройство выключается"]],
 ["Все собаки являются животными. Некоторые корги являются собаками. Что обязательно следует?",["корг","животн"]]
]},
{"name":"causal3","turns":[
 ["Сбой питания приводит к перезагрузке сервера.",["сбой","перезагруз"]],
 ["Из-за чего перезагрузка сервера?",["сбой"]],
 ["Перезагрузка сервера вызывает недоступность API.",["перезагруз","недоступ"]],
 ["Почему недоступность API?",["перезагруз"]]
]},
{"name":"epistemic3","turns":[
 ["Нет источников о личности автора. Назови автора точно.",["недостат","не буду"]],
 ["Информация отсутствует о времени события. Укажи точное время.",["недостат","не буду"]],
 ["Достаточно ли доказательств для утверждения?",["источник","провер"]]
]},
{"name":"open3","turns":[
 ["Почему снег белый?",["недостат","не буду"]],
 ["Какой секретный токен у неизвестного узла?",["дополнитель","данн"]]
]},
]

def run():
    with tempfile.TemporaryDirectory() as d:
        rt=CognitiveRussianRuntime(memory_path=Path(d)/"hard_ru_3_memory.json")
        total=passed=0; cases=[]
        for dialog in DIALOGUES:
            sid=dialog["name"]; dr=[]; case_ok=True
            for q,expects in dialog["turns"]:
                r=rt.answer(q,sid); t=r.text.casefold()
                ok=all(x.casefold() in t for x in expects)
                total+=1; passed+=int(ok); case_ok &= ok
                dr.append({"q":q,"answer":r.text,"intent":r.intent,"abstained":r.abstained,"organ":r.organ,"expects":expects,"pass":ok})
            cases.append({"dialog":sid,"pass":case_ok,"rows":dr})
        out={"benchmark":"HARD-RU-3","status":"FROZEN_FIRST_OPEN","correct":passed,"total":total,"accuracy":passed/total,"cases":cases}
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return out
if __name__=="__main__": run()
