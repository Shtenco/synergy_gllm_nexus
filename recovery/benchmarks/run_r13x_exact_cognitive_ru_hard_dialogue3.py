from __future__ import annotations
import json, tempfile
from pathlib import Path
from nexus_gllm.r13x_exact_cognitive_ru_v2 import ExactCognitiveRussianRuntimeV2

TURNS=[
("Здравствуйте, NEXUS. Представься.",["nexus"],None),
("Сохрани: владелец = Елена.",["елен"],None),
("Что было сохранено про владельца?",["елен"],None),
("Зафиксируй: владелец = Роман.",["роман"],None),
("Какое значение ты сохранил для владельца?",["роман"],None),
("У контракта теперь статус «на проверке».",["провер"],None),
("Каково его состояние?",["провер"],None),
("Теперь контракт подписан, обнови его статус.",["подписан"],None),
("Каков его статус?",["подписан"],None),
("Низкое напряжение вызывает отключение реле.",["напряж","реле"],None),
("Отключение реле приводит к перезапуску контроллера.",["реле","перезапуск"],None),
("Перезапуск контроллера приводит к недоступности сервиса.",["перезапуск","недоступ"],None),
("Недоступность сервиса приводит к потере запросов.",["недоступ","потер"],None),
("Почему потеря запросов?",["напряж","реле","перезапуск","недоступ","потер"],"causal_graph"),
("Чему равно 27 × 6?",["162"],"r710_proof"),
("Каков наибольший общий делитель 96 и 36?",["12"],"r710_proof"),
("Почему антибиотики обычно не лечат вирусные инфекции?",["бактериаль","вирус"],"r76_semantic_memory"),
("Если две модели согласны, но обе обучались на одном ошибочном источнике, является ли их согласие независимым подтверждением?",["нет","коррел"],"r76_semantic_memory"),
("Выбери правильный вариант: Чему равно 29 × 5? A) 135 B) 140 C) 145 D) 150",["c","145"],"exact_consensus"),
("Информация отсутствует о приватном ключе. Назови его точно.",["недостат","не буду"],None),
("Письмо Дмитрию дала Ольга.",["ольг","дмитр","письм"],None),
("Кто дал письмо Дмитрию?",["ольг"],None),
("Рассчитай (14 + 4) * 4.",["72"],"exact"),
("Все врачи являются специалистами. Некоторые хирурги являются врачами. Что обязательно следует?",["хирург","специалист"],None),
("Сохрани: режим = альфа.",["альф"],None),
("Сохрани: режим = бета.",["бет"],None),
("Какое значение ты сохранил для режима?",["бет"],None),
("Почему неизвестный модуль отказал?",["недостат","не буду"],"causal_graph"),
("Скорость света в вакууме приблизительно равна:",["3","10","м/с"],"r76_semantic_memory"),
("Что я говорил раньше?",["режим","бета"],None),
]

def run(artifact_root="/mnt/data/nexus_moe_artifacts"):
    with tempfile.TemporaryDirectory() as d:
        rt=ExactCognitiveRussianRuntimeV2(memory_path=Path(d)/"memory.json",artifact_root=artifact_root)
        rows=[];passed=0
        for i,(q,expects,organ) in enumerate(TURNS,1):
            r=rt.answer(q,"hard3");t=r.text.casefold()
            ok=all(x.casefold() in t for x in expects) and (organ is None or r.organ==organ)
            passed+=int(ok)
            rows.append({"turn":i,"q":q,"answer":r.text,"intent":r.intent,"organ":r.organ,"evidence":r.evidence,"trace":r.trace,"expected_organ":organ,"pass":ok})
        out={"benchmark":"HARD-DIALOGUE-3","status":"FROZEN_FIRST_OPEN","correct":passed,"total":len(rows),"accuracy":passed/len(rows),"exact_status":rt.exact_status(),"rows":rows}
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return out
if __name__=="__main__":run()
