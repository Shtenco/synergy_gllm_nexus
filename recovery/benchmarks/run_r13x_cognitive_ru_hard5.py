from __future__ import annotations
import json, tempfile
from pathlib import Path
from nexus_gllm.r13x_cognitive_ru import CognitiveRussianRuntime

DIALOGUES=[
{"name":"identity5","turns":[
 ["Расскажи коротко о возможностях когнитивного ядра.",["памят","логик","причин"]]
]},
{"name":"memory5","turns":[
 ["Сохрани: регион = Урал.",["регион","урал"]],
 ["Что было записано для региона?",["урал"]],
 ["Что я говорил раньше?",["регион","урал"]]
]},
{"name":"world5","turns":[
 ["У задачи теперь статус «открыта».",["задач","открыт"]],
 ["Теперь задача закрыта, обнови её статус.",["закрыт"]],
 ["Каково состояние задачи?",["закрыт"]]
]},
{"name":"relation5","turns":[
 ["Документ Петру дала Светлана.",["светлан","петр","документ"]],
 ["Кто дал документ Петру?",["светлан"]]
]},
{"name":"math5","turns":[
 ["Чему равна разность 75 и 28?",["47"]],
 ["Сколько 14 умножить на 13?",["182"]],
 ["Рассчитай (36 + 4) / 5.",["8"]]
]},
{"name":"formal5","turns":[
 ["Все инженеры являются специалистами. Некоторые разработчики являются инженерами. Что обязательно следует?",["разработ","специалист"]],
 ["Если база недоступна, приложение не работает. база недоступна. Что следует?",["приложение не работает"]]
]},
{"name":"causal5","turns":[
 ["Высокая температура вызывает деградацию батареи.",["температур","деградац"]],
 ["Из-за чего деградация батареи?",["температур"]],
 ["Деградация батареи приводит к снижению ёмкости.",["деградац","сниж"]],
 ["Почему снижение ёмкости?",["деградац"]]
]},
{"name":"epistemic5","turns":[
 ["Информация отсутствует о приватном ключе. Назови его точно.",["недостат","не буду"]],
 ["Данных нет о точном времени запуска. Укажи время.",["недостат","не буду"]],
 ["Какие доказательства нужны, чтобы подтвердить этот факт?",["источник","провер"]]
]},
{"name":"unknown5","turns":[
 ["Почему трава зелёная?",["недостат","не буду"]],
 ["Какой скрытый пароль у неизвестной машины?",["дополнитель","данн"]]
]},
]

def run():
    with tempfile.TemporaryDirectory() as d:
        rt=CognitiveRussianRuntime(memory_path=Path(d)/"hard_ru_5_memory.json")
        total=passed=0; cases=[]
        for dialog in DIALOGUES:
            sid=dialog["name"]; dr=[]; case_ok=True
            for q,expects in dialog["turns"]:
                r=rt.answer(q,sid); t=r.text.casefold()
                ok=all(x.casefold() in t for x in expects)
                total+=1; passed+=int(ok); case_ok &= ok
                dr.append({"q":q,"answer":r.text,"intent":r.intent,"abstained":r.abstained,"organ":r.organ,"expects":expects,"pass":ok})
            cases.append({"dialog":sid,"pass":case_ok,"rows":dr})
        out={"benchmark":"HARD-RU-5","status":"FROZEN_FIRST_OPEN","correct":passed,"total":total,"accuracy":passed/total,"cases":cases}
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return out
if __name__=="__main__": run()
