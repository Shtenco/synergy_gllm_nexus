from __future__ import annotations
import json, tempfile
from pathlib import Path
from nexus_gllm.r13x_cognitive_ru import CognitiveRussianRuntime

CASES=[
{
 "name":"memory_dialogue",
 "turns":[
  ("Привет!", ["привет","nexus"]),
  ("Запомни: кодовое слово Север.", ["запомнил","север"]),
  ("Какое кодовое слово?", ["север"]),
 ]
},
{
 "name":"world_state",
 "turns":[
  ("Статус заказа теперь оплачен.", ["обновил","оплачен"]),
  ("Статус заказа теперь отменён.", ["обновил","отмен"]),
  ("Какой сейчас статус заказа?", ["отмен"]),
 ]
},
{
 "name":"relation_context",
 "turns":[
  ("Анна передала Борису ключ.", ["анна","борис","ключ"]),
  ("Что произошло?", ["анна","борис","ключ"]),
 ]
},
{
 "name":"arithmetic",
 "turns":[
  ("Посчитай 23 * 7.", ["161"]),
  ("Вычисли (12 + 8) * 3.", ["60"]),
 ]
},
{
 "name":"causal_memory",
 "turns":[
  ("Перегрев приводит к отказу двигателя.", ["перегрев","отказ"]),
  ("Почему отказу двигателя?", ["перегрев"]),
 ]
},
{
 "name":"formal_logic",
 "turns":[
  ("Если идёт дождь, то улица мокрая. идёт дождь. Что следует?", ["улица мокрая"]),
 ]
},
{
 "name":"epistemic",
 "turns":[
  ("Нет данных о точном пароле сервера.", ["недостаточно","не буду"]),
 ]
},
{
 "name":"capabilities",
 "turns":[
  ("Что ты умеешь?", ["памят","состояни","логик","причин"]),
 ]
},
]

def run():
    with tempfile.TemporaryDirectory() as d:
        rt=CognitiveRussianRuntime(memory_path=Path(d)/"memory.json")
        rows=[]; total=0; passed=0
        for case in CASES:
            sid=case["name"]; crows=[]
            for q,expects in case["turns"]:
                total+=1
                r=rt.answer(q,sid)
                text=r.text.casefold()
                ok=all(x.casefold() in text for x in expects)
                passed+=int(ok)
                crows.append({"q":q,"answer":r.text,"intent":r.intent,"abstained":r.abstained,"organ":r.organ,"evidence":r.evidence,"trace":r.trace,"pass":ok})
            rows.append({"case":case["name"],"rows":crows,"pass":all(x["pass"] for x in crows)})
        out={"correct":passed,"total":total,"accuracy":passed/total if total else 0.0,"cases":rows}
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return out
if __name__=="__main__":
    run()
