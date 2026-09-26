from __future__ import annotations
import json, tempfile
from pathlib import Path
from nexus_gllm.r13x_cognitive_ru import CognitiveRussianRuntime

DIALOGUES=[
{"name":"identity","turns":[
 ["Здравствуй. Представься кратко.",["nexus"]],
 ["Что можешь делать с памятью и логикой?",["памят","логик"]]
]},
{"name":"kv_memory","turns":[
 ["Запиши: город = Казань.",["город","казань"]],
 ["Какое значение ты сохранил для город?",["казань"]],
 ["Что я говорил раньше?",["город","казань"]]
]},
{"name":"world_other_entity","turns":[
 ["У заявки теперь статус «проверена».",["заявк","провер"]],
 ["Теперь заявка одобрена, обнови её статус.",["одобрен"]],
 ["В каком состоянии заявка сейчас?",["одобрен"]]
]},
{"name":"transfer_case_1","turns":[
 ["Книгу Марии дала Елена.",["елен","мари","книг"]],
 ["Что произошло?",["елен","мари","книг"]]
]},
{"name":"transfer_case_2","turns":[
 ["От Сергея Павел получил пакет.",["серге","павел","пакет"]],
 ["Кто передал пакет Павлу?",["серге"]]
]},
{"name":"math_words","turns":[
 ["Сколько 35 умножить на 4?",["140"]],
 ["Чему равно 81 разделить на 9?",["9"]],
 ["Чему равна разность 90 и 37?",["53"]]
]},
{"name":"formal_case","turns":[
 ["Все птицы являются животными. Некоторые вороны являются птицами. Что обязательно следует?",["ворон","животн"]]
]},
{"name":"causal_chain","turns":[
 ["Дефицит охлаждения является причиной перегрева.",["дефицит","перегрев"]],
 ["По какой причине перегрев?",["дефицит"]],
 ["Перегрев приводит к аварийному отключению.",["перегрев","аварийн"]],
 ["Почему аварийное отключение?",["перегрев"]]
]},
{"name":"epistemic_new","turns":[
 ["Информация отсутствует о секретном ключе. Назови его точно.",["недостат","не буду"]],
 ["Нет наблюдений температуры, но требуется точное значение.",["недостат","не буду"]],
 ["Проверить источник утверждения: что для этого нужно?",["источник","провер"]]
]},
{"name":"open_unknown","turns":[
 ["Почему небо голубое?",["недостат","не буду"]],
 ["Какой пароль у неизвестного сервера?",["дополнитель","данн"]]
]},
]

def run():
    with tempfile.TemporaryDirectory() as d:
        rt=CognitiveRussianRuntime(memory_path=Path(d)/"hard_ru_2_memory.json")
        total=passed=0; cases=[]
        for dialog in DIALOGUES:
            sid=dialog["name"]; dr=[]; case_ok=True
            for q,expects in dialog["turns"]:
                r=rt.answer(q,sid); t=r.text.casefold()
                ok=all(x.casefold() in t for x in expects)
                total+=1; passed+=int(ok); case_ok &= ok
                dr.append({"q":q,"answer":r.text,"intent":r.intent,"abstained":r.abstained,"organ":r.organ,"expects":expects,"pass":ok})
            cases.append({"dialog":sid,"pass":case_ok,"rows":dr})
        out={"benchmark":"HARD-RU-2","status":"FROZEN_FIRST_OPEN","correct":passed,"total":total,"accuracy":passed/total,"cases":cases}
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return out
if __name__=="__main__": run()
