from __future__ import annotations
import json, tempfile
from pathlib import Path
from nexus_gllm.r13x_exact_cognitive_ru_v2 import ExactCognitiveRussianRuntimeV2

TURNS=[
("Доброе утро, NEXUS. Представься.",["nexus"],None),
("Сохрани: куратор = София.",["софи"],None),
("Что было сохранено про куратора?",["софи"],None),
("Зафиксируй: куратор = Артём.",["артем"],None),
("Какое значение ты сохранил для кураторе?",["артем"],None),
("У задачи теперь статус «назначена».",["назнач"],None),
("Каково её состояние?",["назнач"],None),
("Теперь задача выполнена, обнови её статус.",["выполн"],None),
("Каков её статус?",["выполн"],None),
("Повреждение кабеля вызывает потерю связи.",["поврежд","потер"],None),
("Потеря связи приводит к недоступности узла.",["потер","недоступ"],None),
("Недоступность узла приводит к ошибке синхронизации.",["недоступ","ошиб"],None),
("Ошибка синхронизации приводит к остановке репликации.",["ошиб","останов"],None),
("Почему остановка репликации?",["поврежд","потер","недоступ","ошиб","останов"],"causal_graph"),
("Чему равно 31 × 7?",["217"],"r710_proof"),
("Каков наибольший общий делитель 105 и 45?",["15"],"r710_proof"),
("Какова средняя асимптотическая сложность поиска элемента по ключу в хорошо реализованной хеш-таблице?",["o(1)"],"r76_semantic_memory"),
("Какое слово является антонимом к слову «увеличивать» в нейтральном значении размера/величины?",["уменьш"],"r76_semantic_memory"),
("Выбери правильный вариант: Чему равно 24 × 6? A) 124 B) 134 C) 139 D) 144",["d","144"],"exact_consensus"),
("Нет данных о секретном идентификаторе. Назови его точно.",["недостат","не буду"],None),
("Карту Виктору дала Нина.",["нин","виктор","карт"],None),
("Кто дал карту Виктору?",["нин"],None),
("Рассчитай (20 - 5) * 5.",["75"],"exact"),
("Все аналитики являются специалистами. Некоторые аудиторы являются аналитиками. Что обязательно следует?",["аудитор","специалист"],None),
("Сохрани: цвет = зелёный.",["зелен"],None),
("Сохрани: цвет = красный.",["красн"],None),
("Какое значение ты сохранил для цвета?",["красн"],None),
("Почему неизвестный процесс завершился?",["недостат","не буду"],"causal_graph"),
("Система выбирает между ответом внешней модели и проверенным формальным доказательством, и они противоречат друг другу. Какой источник должен иметь приоритет в архитектуре NEXUS-надсистемы?",["формальн","authority"],"r76_semantic_memory"),
("Что я говорил раньше?",["цвет","красн"],None),
]

def run(artifact_root="/mnt/data/nexus_moe_artifacts"):
    with tempfile.TemporaryDirectory() as d:
        rt=ExactCognitiveRussianRuntimeV2(memory_path=Path(d)/"memory.json",artifact_root=artifact_root)
        rows=[];passed=0
        for i,(q,expects,organ) in enumerate(TURNS,1):
            r=rt.answer(q,"hard4");t=r.text.casefold()
            ok=all(x.casefold() in t for x in expects) and (organ is None or r.organ==organ)
            passed+=int(ok)
            rows.append({"turn":i,"q":q,"answer":r.text,"intent":r.intent,"organ":r.organ,"evidence":r.evidence,"trace":r.trace,"expected_organ":organ,"pass":ok})
        out={"benchmark":"HARD-DIALOGUE-4","status":"FROZEN_FIRST_OPEN","correct":passed,"total":len(rows),"accuracy":passed/len(rows),"exact_status":rt.exact_status(),"rows":rows}
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return out
if __name__=="__main__":run()
