from __future__ import annotations
import json, tempfile
from collections import Counter
from pathlib import Path
from nexus_gllm.r13x_exact_cognitive_ru_v2 import ExactCognitiveRussianRuntimeV2

def norm(s:str)->str:
    return s.casefold().replace("ё","е")

TURNS=[
("Здравствуйте! Назови себя.",["nexus"],None),
("Сохрани: менеджер = Юлия.",["юли"],None),
("Что было сохранено про менеджера?",["юли"],None),
("Сохрани: менеджер = Денис.",["денис"],None),
("Какое значение ты сохранил для менеджере?",["денис"],None),
("У сборки теперь статус «тестирование».",["тестирован"],None),
("Каково её состояние?",["тестирован"],None),
("Теперь сборка выпущена, обнови её статус.",["выпущен"],None),
("Каков её статус?",["выпущен"],None),
("Повреждение диска вызывает ошибку чтения.",["поврежд","ошиб"],None),
("Ошибка чтения приводит к сбою базы.",["ошиб","сбой"],None),
("Сбой базы приводит к недоступности API.",["сбой","недоступ"],None),
("Недоступность API приводит к отказу клиента.",["недоступ","отказ"],None),
("Почему отказ клиента?",["поврежд","ошиб","сбой","недоступ","отказ"],"causal_graph"),
("Чему равно 42 × 5?",["210"],"r710_proof"),
("Каков наибольший общий делитель 144 и 60?",["12"],"r710_proof"),
("При 25 °C водный раствор с pH=3 является:",["кисл"],"r76_semantic_memory"),
("В Python чему равно len(list(range(2, 10, 2)))?",["5"],"r76_semantic_memory"),
("Выбери правильный вариант: Чему равно 16 × 9? A) 134 B) 144 C) 154 D) 164",["b","144"],"exact_consensus"),
("Логов нет о точном идентификаторе запуска. Назови его точно.",["недостат","не буду"],None),
("Файл Сергею дала Анна.",["анн","серге","файл"],None),
("Кто дал файл Сергею?",["анн"],None),
("Рассчитай (18 - 6) * 7.",["84"],"exact"),
("Все исследователи являются специалистами. Некоторые физики являются исследователями. Что обязательно следует?",["физик","специалист"],None),
("Сохрани: канал = основной.",["основн"],None),
("Сохрани: канал = резервный.",["резервн"],None),
("Какое значение ты сохранил для канале?",["резервн"],None),
("Почему неизвестный процесс аварийно завершился?",["недостат","не буду"],"causal_graph"),
("В предложении «Несмотря на дождь, поездка состоялась» оборот «несмотря на дождь» выражает:",["уступ"],"r76_semantic_memory"),
("Что я говорил раньше?",["канал","резервн"],None),
]

def run(artifact_root="/mnt/data/nexus_moe_artifacts"):
    with tempfile.TemporaryDirectory() as d:
        rt=ExactCognitiveRussianRuntimeV2(memory_path=Path(d)/"memory.json",artifact_root=artifact_root)
        rows=[];passed=0
        for i,(q,expects,organ) in enumerate(TURNS,1):
            r=rt.answer(q,"hard6");t=norm(r.text)
            ok=all(norm(x) in t for x in expects) and (organ is None or r.organ==organ)
            passed+=int(ok)
            rows.append({"turn":i,"q":q,"answer":r.text,"intent":r.intent,"organ":r.organ,"evidence":r.evidence,"trace":r.trace,"expected_organ":organ,"pass":ok})
        counts=Counter(x["organ"] for x in rows)
        r714=sum(any(str(t).startswith("r714_lang=") for t in x["trace"]) or "r714_morpholex" in x["evidence"] for x in rows)
        out={"benchmark":"HARD-DIALOGUE-6","status":"FROZEN_FIRST_OPEN_NO_POST_TUNING","correct":passed,"total":len(rows),"accuracy":passed/len(rows),"exact_status":rt.exact_status(),"organ_counts":dict(counts),"r714_provenance_turns":r714,"rows":rows}
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return out
if __name__=="__main__":run()
