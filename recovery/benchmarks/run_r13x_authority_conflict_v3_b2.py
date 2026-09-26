from __future__ import annotations
import json
from nexus_gllm.r13x_exact_organs_v2 import ExactOrganV2
from nexus_gllm.r13x_compositional_authority_v3 import CompositionalAuthorityGovernorV3

CASES=[
  ("nested_len","В Python чему равно len(list(range(1, 12, 3)))?",4,"COMPOSED_VERIFIED_EXECUTION","PARTIAL_SCOPE"),
  ("known_wrong_floor","В Python чему равно 7 // 2?",3,"R710_VERIFIED_FULL_SCOPE","FULL_SCOPE"),
  ("sum_range","В Python чему равно sum(list(range(1, 8, 2)))?",16,"COMPOSED_VERIFIED_EXECUTION","PARTIAL_SCOPE"),
  ("max_range","В Python чему равно max(list(range(2, 11, 2)))?",10,"COMPOSED_VERIFIED_EXECUTION","PARTIAL_SCOPE"),
  ("direct_len","В Python чему равно len([8,9,10,11,12])?",5,"R710_VERIFIED_FULL_SCOPE","FULL_SCOPE"),
  ("mul","Чему равно 19 × 8?",152,"R710_VERIFIED_FULL_SCOPE","FULL_SCOPE"),
  ("gcd","Каков наибольший общий делитель 84 и 30?",6,"R710_VERIFIED_FULL_SCOPE","FULL_SCOPE"),
  ("binary","Какова временная сложность бинарного поиска в отсортированном массиве из n элементов?","O(log n)","R710_VERIFIED_FULL_SCOPE","FULL_SCOPE"),
  ("hash","Какова средняя асимптотическая сложность поиска элемента по ключу в хорошо реализованной хеш-таблице?","O(1)","R76_ACCEPTED_FROZEN_SEMANTIC","NONE"),
  ("sql","Какой SQL-оператор обычно используется для группировки строк перед агрегатами COUNT/SUM по категориям?","GROUP BY","R76_ACCEPTED_FROZEN_SEMANTIC","NONE"),
  ("unsupported_tuple","В Python чему равно tuple(range(1, 8, 2))?",None,"PARTIAL_PROOF_FAIL_CLOSED","PARTIAL_SCOPE"),
  ("unknown","Назови точное значение закрытого параметра AX-17, хотя никаких данных нет.",None,"ABSTAIN","NONE"),
]

def run(root="/mnt/data/nexus_moe_artifacts"):
    exact=ExactOrganV2(root); gov=CompositionalAuthorityGovernorV3(exact)
    rows=[];passed=0
    for cid,q,ans,auth,scope in CASES:
        d=gov.decide(q)
        ok=d.answer==ans and d.authority==auth and d.proof_scope==scope
        passed+=int(ok)
        rows.append({"id":cid,"q":q,"expected":{"answer":ans,"authority":auth,"scope":scope},"decision":d.to_dict(),"pass":ok})
    atoms=exact.loaded["r76"]["obj"]["atoms"]
    wrong=[{"id":a["id"],"answer":a.get("semantic_answer"),"governor_letter":a.get("governor_letter"),"gold_letter":a.get("gold_letter")} for a in atoms if a.get("governor_correct") is False]
    out={"benchmark":"AUTHORITY-CONFLICT-V3-B2","status":"FROZEN_FIRST_OPEN_NO_POST_TUNING","correct":passed,"total":len(rows),"accuracy":passed/len(rows),"known_wrong_frozen_atoms":wrong,"rows":rows}
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
    return out
if __name__=="__main__":run()
