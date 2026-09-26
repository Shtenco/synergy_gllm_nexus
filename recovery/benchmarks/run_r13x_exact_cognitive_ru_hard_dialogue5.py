from __future__ import annotations
import json, tempfile
from collections import Counter
from pathlib import Path
from nexus_gllm.r13x_exact_cognitive_ru_v2 import ExactCognitiveRussianRuntimeV2

def norm(s:str)->str:
    return s.casefold().replace("ё","е")

TURNS=[
("Доброе утро! Кто ты?",["nexus"],None),
("Сохрани: ответственный = Алёна.",["ален"],None),
("Что было сохранено про ответственного?",["ален"],None),
("Зафиксируй: ответственный = Борис.",["борис"],None),
("Какое значение ты сохранил для ответственном?",["борис"],None),
("У релиза теперь статус «кандидат».",["кандидат"],None),
("Каково его состояние?",["кандидат"],None),
("Теперь релиз опубликован, обнови его статус.",["опубликован"],None),
("Каков его статус?",["опубликован"],None),
("Ошибка конфигурации вызывает сбой запуска.",["конфигурац","сбой"],None),
("Сбой запуска приводит к недоступности сервиса.",["сбой","недоступ"],None),
("Недоступность сервиса приводит к отказу проверки.",["недоступ","отказ"],None),
("Отказ проверки приводит к блокировке релиза.",["отказ","блокиров"],None),
("Почему блокировка релиза?",["конфигурац","сбой","недоступ","отказ","блокиров"],"causal_graph"),
("Чему равно 37 × 4?",["148"],"r710_proof"),
("Каков наибольший общий делитель 126 и 54?",["18"],"r710_proof"),
("Лунные фазы возникают главным образом из-за:",["освещ","лун"],"r76_semantic_memory"),
("Какие основания комплементарны в обычной двуцепочечной ДНК?",["a–t","c–g"],"r76_semantic_memory"),
("Выбери правильный вариант: Чему равно 18 × 8? A) 128 B) 136 C) 144 D) 152",["c","144"],"exact_consensus"),
("Нет журналов о точном времени запуска. Назови время точно.",["недостат","не буду"],None),
("Пакет Олегу дала Вера.",["вер","олег","пакет"],None),
("Кто дал пакет Олегу?",["вер"],None),
("Рассчитай (11 + 9) * 5.",["100"],"exact"),
("Все архитекторы являются специалистами. Некоторые проектировщики являются архитекторами. Что обязательно следует?",["проектиров","специалист"],None),
("Сохрани: приоритет = высокий.",["высок"],None),
("Сохрани: приоритет = низкий.",["низк"],None),
("Какое значение ты сохранил для приоритете?",["низк"],None),
("Почему неизвестный компонент завис?",["недостат","не буду"],"causal_graph"),
("Какое слово наиболее точно означает «способность системы восстанавливаться после нарушения»?",["устойчив","резилиент"],"r76_semantic_memory"),
("Что я говорил раньше?",["приоритет","низк"],None),
]

def run(artifact_root="/mnt/data/nexus_moe_artifacts"):
    with tempfile.TemporaryDirectory() as d:
        rt=ExactCognitiveRussianRuntimeV2(memory_path=Path(d)/"memory.json",artifact_root=artifact_root)
        rows=[];passed=0
        for i,(q,expects,organ) in enumerate(TURNS,1):
            r=rt.answer(q,"hard5");t=norm(r.text)
            ok=all(norm(x) in t for x in expects) and (organ is None or r.organ==organ)
            passed+=int(ok)
            rows.append({"turn":i,"q":q,"answer":r.text,"intent":r.intent,"organ":r.organ,"evidence":r.evidence,"trace":r.trace,"expected_organ":organ,"pass":ok})
        counts=Counter(x["organ"] for x in rows)
        r714=sum(any(str(t).startswith("r714_lang=") for t in x["trace"]) or "r714_morpholex" in x["evidence"] for x in rows)
        out={"benchmark":"HARD-DIALOGUE-5","status":"FROZEN_FIRST_OPEN_NO_POST_TUNING","correct":passed,"total":len(rows),"accuracy":passed/len(rows),"exact_status":rt.exact_status(),"organ_counts":dict(counts),"r714_provenance_turns":r714,"rows":rows}
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return out
if __name__=="__main__":run()
