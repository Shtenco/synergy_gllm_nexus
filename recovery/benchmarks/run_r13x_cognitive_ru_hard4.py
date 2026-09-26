from __future__ import annotations
import json, tempfile
from pathlib import Path
from nexus_gllm.r13x_cognitive_ru import CognitiveRussianRuntime

DIALOGUES=[
{"name":"identity4","turns":[
 ["Здравствуйте, вы NEXUS?",["nexus"]],
 ["Кратко: что умеет твоё когнитивное ядро?",["памят","логик","причин"]]
]},
{"name":"memory4","turns":[
 ["Зафиксируй — оператор = Алина.",["оператор","алина"]],
 ["Что было записано для оператора?",["алина"]],
 ["Что я говорил раньше?",["оператор","алина"]]
]},
{"name":"world4","turns":[
 ["У отчёта теперь статус «черновик».",["отчет","черновик"]],
 ["Теперь отчёт утверждён, обнови его статус.",["утвержден"]],
 ["Каково состояние отчёта?",["утвержден"]]
]},
{"name":"relation4","turns":[
 ["Ключ Николаю дала Вера.",["вер","никола","ключ"]],
 ["Кто дал ключ Николаю?",["вер"]]
]},
{"name":"math4","turns":[
 ["Чему равна сумма 123 и 77?",["200"]],
 ["Сколько 16 умножить на 12?",["192"]],
 ["Вычисли (50 - 8) / 7.",["6"]]
]},
{"name":"formal4","turns":[
 ["Все программисты являются специалистами. Некоторые стажёры являются программистами. Что обязательно следует?",["стаж","специалист"]],
 ["Если питание отключено, система недоступна. питание отключено. Что следует?",["система недоступна"]]
]},
{"name":"causal4","turns":[
 ["Высокая нагрузка вызывает задержку сети.",["нагруз","задерж"]],
 ["По какой причине задержка сети?",["нагруз"]],
 ["Задержка сети приводит к таймауту API.",["задерж","таймаут"]],
 ["Почему таймаут API?",["задерж"]]
]},
{"name":"epistemic4","turns":[
 ["Данных нет о закрытом ключе. Сообщи его точно.",["недостат","не буду"]],
 ["Нет наблюдений о температуре. Назови точное значение.",["недостат","не буду"]],
 ["Какие доказательства нужны для подтверждения факта?",["источник","провер"]]
]},
{"name":"history4","turns":[
 ["Сохрани — номер проекта = 42.",["номер проекта","42"]],
 ["Что я сказал раньше?",["номер проекта","42"]]
]},
{"name":"unknown4","turns":[
 ["Почему океан солёный?",["недостат","не буду"]],
 ["Какой секрет у неизвестного узла?",["дополнитель","данн"]]
]},
]

def run():
    with tempfile.TemporaryDirectory() as d:
        rt=CognitiveRussianRuntime(memory_path=Path(d)/"hard_ru_4_memory.json")
        total=passed=0; cases=[]
        for dialog in DIALOGUES:
            sid=dialog["name"]; dr=[]; case_ok=True
            for q,expects in dialog["turns"]:
                r=rt.answer(q,sid); t=r.text.casefold()
                ok=all(x.casefold() in t for x in expects)
                total+=1; passed+=int(ok); case_ok &= ok
                dr.append({"q":q,"answer":r.text,"intent":r.intent,"abstained":r.abstained,"organ":r.organ,"expects":expects,"pass":ok})
            cases.append({"dialog":sid,"pass":case_ok,"rows":dr})
        out={"benchmark":"HARD-RU-4","status":"FROZEN_FIRST_OPEN","correct":passed,"total":total,"accuracy":passed/total,"cases":cases}
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return out
if __name__=="__main__": run()
