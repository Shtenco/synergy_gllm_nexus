from __future__ import annotations
import json, tempfile
from pathlib import Path
from nexus_gllm.r13x_exact_cognitive_ru_v2 import ExactCognitiveRussianRuntimeV2

TURNS=[
("Привет! Кто ты?",["nexus"],None),
("Сохрани: проект = Атлас.",["атлас"],None),
("Какое значение ты сохранил для проект?",["атлас"],None),
("Сохрани: проект = Орион.",["орион"],None),
("Что было сохранено про проект?",["орион"],None),
("Статус сервера теперь готов.",["готов"],None),
("Каково его состояние?",["готов"],None),
("Теперь сервер отключён, обнови его статус.",["отключ"],None),
("Каков его статус?",["отключ"],None),
("Высокая нагрузка вызывает перегрев.",["нагруз","перегрев"],None),
("Перегрев приводит к троттлингу.",["перегрев","троттл"],None),
("Троттлинг приводит к падению производительности.",["троттл","падени"],None),
("Почему падение производительности?",["нагруз","перегрев","троттл","падени"],"causal_graph"),
("Чему равно 23 × 7?",["161"],"r710_proof"),
("Каков наибольший общий делитель 48 и 18?",["6"],"r710_proof"),
("Зачем нужен регрессионный тест?",["сломалось","работав"],"r76_semantic_memory"),
("Какой тип обратной связи обычно стабилизирует систему около заданного значения?",["отрицатель"],"r76_semantic_memory"),
("Выбери правильный вариант: Чему равно 23 × 7? A) 151 B) 161 C) 171 D) 181",["b","161"],"exact_consensus"),
("Нет источников о точном пароле узла. Назови его.",["недостат","не буду"],None),
("У отчёта теперь статус «черновик».",["черновик"],None),
("Теперь отчёт утверждён, обнови его статус.",["утвержден"],None),
("Каково его состояние?",["утвержден"],None),
("Анна передала Борису ключ.",["анна","борис","ключ"],None),
("Что произошло?",["анна","борис","ключ"],None),
("Посчитай (12 + 8) * 3.",["60"],"r710_proof"),
("Все кошки являются млекопитающими. Некоторые сфинксы являются кошками. Что обязательно следует?",["сфинкс","млекопита"],None),
("Сохрани: режим = автоматический.",["автомат"],None),
("Сохрани: режим = ручной.",["ручной"],None),
("Какое значение ты сохранил для режим?",["ручной"],None),
("Почему неизвестное событие произошло?",["недостат","не буду"],None),
]

def run(root="/mnt/data/nexus_moe_artifacts"):
    with tempfile.TemporaryDirectory() as d:
        rt=ExactCognitiveRussianRuntimeV2(memory_path=Path(d)/"mem.json",artifact_root=root)
        rows=[];okn=0
        for i,(q,expects,organ) in enumerate(TURNS,1):
            r=rt.answer(q,"long")
            t=r.text.casefold(); ok=all(x.casefold() in t for x in expects)
            if organ is not None: ok=ok and r.organ==organ
            okn+=int(ok)
            rows.append({"turn":i,"q":q,"answer":r.text,"intent":r.intent,"organ":r.organ,"evidence":r.evidence,"trace":r.trace,"expects":expects,"expected_organ":organ,"pass":ok})
        out={"benchmark":"HARD-DIALOGUE-1","status":"FROZEN_FIRST_OPEN","exact_status":rt.exact_status(),"correct":okn,"total":len(rows),"accuracy":okn/len(rows),"rows":rows}
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return out
if __name__=="__main__":run()
