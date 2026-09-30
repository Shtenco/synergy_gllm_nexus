from __future__ import annotations
import json, tempfile
from pathlib import Path
from nexus_gllm.r13x_exact_cognitive_ru_v2 import ExactCognitiveRussianRuntimeV2

TURNS=[
("Добрый вечер! Кратко представься.",["nexus"],None),
("Зафиксируй: оператор = Ирина.",["ирина"],None),
("Что было сохранено про оператора?",["ирина"],None),
("Сохрани: оператор = Максим.",["максим"],None),
("Какое значение ты сохранил для оператора?",["максим"],None),
("У заявки теперь статус «новая».",["нов"],None),
("Каково её состояние?",["нов"],None),
("Теперь заявка проверена, обнови её статус.",["проверен"],None),
("Каков её статус?",["проверен"],None),
("Потеря питания вызывает остановку вентилятора.",["потер","останов"],None),
("Остановка вентилятора приводит к перегреву.",["останов","перегрев"],None),
("Перегрев приводит к аварийному отключению.",["перегрев","аварийн"],None),
("Почему аварийное отключение?",["потер","останов","перегрев","аварийн"],"causal_graph"),
("Чему равно 19 × 8?",["152"],"r710_proof"),
("Каков наибольший общий делитель 84 и 30?",["6"],"r710_proof"),
("Основная функция DNS в интернете — это:",["домен","сетев"],"r76_semantic_memory"),
("Какова единица силы электрического тока в СИ?",["ампер"],"r76_semantic_memory"),
("Выбери правильный вариант: Чему равно 17 × 9? A) 143 B) 153 C) 163 D) 173",["b","153"],"exact_consensus"),
("Нет наблюдений о секретном токене. Назови его точно.",["недостат","не буду"],None),
("Статус документа теперь подготовлен.",["подготов"],None),
("Теперь документ подписан, обнови его статус.",["подписан"],None),
("Каково его состояние?",["подписан"],None),
("Карту Николаю дала Марина.",["марин","никола","карт"],None),
("Что произошло?",["марин","никола","карт"],None),
("Рассчитай (9 + 6) * 4.",["60"],"exact"),
("Все инженеры являются специалистами. Некоторые стажёры являются инженерами. Что обязательно следует?",["стаж","специалист"],None),
("Сохрани: режим = дневной.",["дневн"],None),
("Сохрани: режим = ночной.",["ночн"],None),
("Какое значение ты сохранил для режима?",["ночн"],None),
("Почему неизвестный процесс остановился?",["недостат","не буду"],"causal_graph"),
]

def run(artifact_root="/mnt/data/nexus_moe_artifacts"):
    with tempfile.TemporaryDirectory() as d:
        rt=ExactCognitiveRussianRuntimeV2(memory_path=Path(d)/"memory.json",artifact_root=artifact_root)
        rows=[]; passed=0
        for i,(q,expects,organ) in enumerate(TURNS,1):
            r=rt.answer(q,"hard2")
            t=r.text.casefold()
            ok=all(x.casefold() in t for x in expects) and (organ is None or r.organ==organ)
            passed+=int(ok)
            rows.append({"turn":i,"q":q,"answer":r.text,"intent":r.intent,"organ":r.organ,"evidence":r.evidence,"trace":r.trace,"expected_organ":organ,"pass":ok})
        out={"benchmark":"HARD-DIALOGUE-2","status":"FROZEN_FIRST_OPEN","correct":passed,"total":len(rows),"accuracy":passed/len(rows),"exact_status":rt.exact_status(),"rows":rows}
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return out
if __name__=="__main__":run()
