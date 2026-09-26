from __future__ import annotations
import json
from nexus_gllm.r13x_exact_organs_v2 import ExactOrganV2
from nexus_gllm.r13x_compositional_authority_v3 import CompositionalAuthorityGovernorV3

CASES=[
  {
    "id":"known_wrong_nested_len",
    "q":"В Python чему равно len(list(range(2, 10, 2)))?",
    "answer":4,
    "authority":"COMPOSED_VERIFIED_EXECUTION",
    "scope":"PARTIAL_SCOPE"
  },
  {
    "id":"known_wrong_floordiv",
    "q":"В Python чему равно 7 // 2?",
    "answer":3,
    "authority":"R710_VERIFIED_FULL_SCOPE",
    "scope":"FULL_SCOPE"
  },
  {
    "id":"accepted_hash_table",
    "q":"Какова средняя асимптотическая сложность поиска элемента по ключу в хорошо реализованной хеш-таблице?",
    "answer":"O(1)",
    "authority":"R76_ACCEPTED_FROZEN_SEMANTIC",
    "scope":"NONE"
  },
  {
    "id":"accepted_binary_search",
    "q":"Какова временная сложность бинарного поиска в отсортированном массиве из n элементов?",
    "answer":"O(log n)",
    "authority":"R76_ACCEPTED_FROZEN_SEMANTIC",
    "scope":"NONE"
  },
  {
    "id":"accepted_sql_group",
    "q":"Какой SQL-оператор обычно используется для группировки строк перед агрегатами COUNT/SUM по категориям?",
    "answer":"GROUP BY",
    "authority":"R76_ACCEPTED_FROZEN_SEMANTIC",
    "scope":"NONE"
  },
  {
    "id":"full_arithmetic",
    "q":"Чему равно 23 × 7?",
    "answer":161,
    "authority":"R710_VERIFIED_FULL_SCOPE",
    "scope":"FULL_SCOPE"
  },
  {
    "id":"full_gcd",
    "q":"Каков наибольший общий делитель 48 и 18?",
    "answer":6,
    "authority":"R710_VERIFIED_FULL_SCOPE",
    "scope":"FULL_SCOPE"
  },
  {
    "id":"safe_sum_composition",
    "q":"В Python чему равно sum(list(range(2, 10, 2)))?",
    "answer":20,
    "authority":"COMPOSED_VERIFIED_EXECUTION",
    "scope":"PARTIAL_SCOPE"
  },
  {
    "id":"safe_list_composition",
    "q":"В Python чему равно list(range(2, 10, 2))?",
    "answer":[2,4,6,8],
    "authority":"COMPOSED_VERIFIED_EXECUTION",
    "scope":"PARTIAL_SCOPE"
  },
  {
    "id":"unsupported_outer_tuple",
    "q":"В Python чему равно tuple(range(2, 10, 2))?",
    "answer":None,
    "authority":"PARTIAL_PROOF_FAIL_CLOSED",
    "scope":"PARTIAL_SCOPE"
  },
  {
    "id":"unknown",
    "q":"Каково точное значение неизвестного закрытого параметра QX-991 без данных?",
    "answer":None,
    "authority":"ABSTAIN",
    "scope":"NONE"
  }
]

def run(root="/mnt/data/nexus_moe_artifacts"):
    exact=ExactOrganV2(root)
    gov=CompositionalAuthorityGovernorV3(exact)
    atoms=exact.loaded["r76"]["obj"]["atoms"]
    known_wrong=[
        {
            "id":a["id"],
            "question":a.get("question"),
            "semantic_answer":a.get("semantic_answer"),
            "governor_letter":a.get("governor_letter"),
            "gold_letter":a.get("gold_letter")
        }
        for a in atoms if a.get("governor_correct") is False
    ]
    rows=[];passed=0
    for case in CASES:
        d=gov.decide(case["q"])
        ok=(
            d.answer==case["answer"]
            and d.authority==case["authority"]
            and d.proof_scope==case["scope"]
        )
        passed+=int(ok)
        rows.append({"case":case, "decision":d.to_dict(), "pass":ok})
    out={
      "benchmark":"AUTHORITY-CONFLICT-V3",
      "status":"FROZEN_FIRST_OPEN",
      "exact_status":exact.status(),
      "known_wrong_frozen_atoms":known_wrong,
      "correct":passed,
      "total":len(rows),
      "accuracy":passed/len(rows),
      "rows":rows
    }
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
    return out

if __name__=="__main__":run()
