from __future__ import annotations
import json, tempfile
from pathlib import Path
from nexus_gllm.r13x_cognitive_ru import CognitiveRussianRuntime

DIALOGUES=[
{"name":"greeting_and_capability","turns":[
 ["Доброе утро. Кто ты и что можешь?",["nexus","памят"]],
 ["Можешь ли ты не выдумывать, если информации мало?",["данных","недостат"]]
]},
{"name":"memory_paraphrase","turns":[
 ["Зафиксируй кодовое слово Восток.",["восток"]],
 ["Напомни мне кодовое слово.",["восток"]],
 ["Что я сказал до этого?",["кодовое","восток"]]
]},
{"name":"memory_key_value","turns":[
 ["Сохрани: проект = Альтаир.",["проект","альтаир"]],
 ["Что ты запомнил про проект?",["альтаир"]]
]},
{"name":"world_morphology","turns":[
 ["У заказа теперь статус «собран».",["собран"]],
 ["Теперь заказ отправлен, обнови его статус.",["отправ"]],
 ["В каком состоянии заказ сейчас?",["отправ"]]
]},
{"name":"relation_surface","turns":[
 ["Иван вручил Марии книгу.",["иван","мари","книг"]],
 ["Что случилось?",["иван","мари","книг"]]
]},
{"name":"relation_receive","turns":[
 ["Мария получила книгу от Ивана.",["иван","мари","книг"]],
 ["Кто передал книгу Марии?",["иван"]]
]},
{"name":"arithmetic_ru","turns":[
 ["Сколько составляет 18 умножить на 7?",["126"]],
 ["Чему равна сумма 45 и 17?",["62"]],
 ["Посчитай 144 / 12.",["12"]]
]},
{"name":"formal_variants","turns":[
 ["Если сервер выключен, сервис недоступен. Сервер выключен. Значит ли это, что сервис недоступен?",["сервис","недоступ"]],
 ["Все кошки являются млекопитающими. Некоторые сфинксы являются кошками. Что обязательно следует?",["сфинкс","млекопита"]]
]},
{"name":"causal_variants","turns":[
 ["Недостаток масла вызывает перегрев двигателя.",["масл","перегрев"]],
 ["Из-за чего возникает перегрев двигателя?",["масл"]],
 ["Перегрев двигателя приводит к отказу насоса.",["перегрев","отказ"]],
 ["Почему произошёл отказ насоса?",["перегрев"]]
]},
{"name":"epistemic_variants","turns":[
 ["Мы ничего не знаем о пароле. Назови его точно.",["недостат","не буду"]],
 ["Источников нет, но дай точную дату события.",["недостат","не буду"]],
 ["Какие доказательства нужны, чтобы подтвердить утверждение?",["источник","провер"]]
]},
{"name":"context_history","turns":[
 ["Запомни: любимый цвет = синий.",["синий"]],
 ["Привет ещё раз.",["привет"]],
 ["Какой любимый цвет я просил сохранить?",["синий"]]
]},
]

def run():
    with tempfile.TemporaryDirectory() as d:
        rt=CognitiveRussianRuntime(memory_path=Path(d)/"hard_ru_1_memory.json")
        total=passed=0; rows=[]; cases=[]
        for dialog in DIALOGUES:
            sid=dialog["name"]; dr=[]; case_ok=True
            for q,expects in dialog["turns"]:
                r=rt.answer(q,sid); t=r.text.casefold()
                ok=all(x.casefold() in t for x in expects)
                total+=1; passed+=int(ok); case_ok &= ok
                row={"q":q,"answer":r.text,"intent":r.intent,"abstained":r.abstained,"organ":r.organ,"expects":expects,"pass":ok}
                rows.append({"dialog":sid,**row}); dr.append(row)
            cases.append({"dialog":sid,"pass":case_ok,"rows":dr})
        out={"benchmark":"HARD-RU-1","status":"CONSUMED_AFTER_FIRST_RUN","correct":passed,"total":total,"accuracy":passed/total,"cases":cases}
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return out
if __name__=="__main__": run()
