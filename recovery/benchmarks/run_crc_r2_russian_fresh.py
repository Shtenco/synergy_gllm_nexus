from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from nexus_gllm.r13x_exact_cognitive_ru_v2 import ExactCognitiveRussianRuntimeV2

OUT = Path("artifacts/crc_r2_russian_fresh")
OUT.mkdir(parents=True, exist_ok=True)

# Frozen before first execution. These prompts are new and are not copied from the
# historical HARD-DIALOGUE suites. Runtime source is intentionally unchanged.
SCENARIOS = [
    {
        "id": "memory_lifecycle",
        "capability": "memory",
        "turns": [
            {"u": "Запомни: ключ проекта = орбита-47.", "intent": "memory_store", "contains": ["орбита-47"], "memory_changed": True},
            {"u": "Какой ключ проекта я просил сохранить?", "intent": "memory_recall", "contains": ["орбита-47"], "abstained": False},
            {"u": "Запомни: резервный маркер = кедр-19.", "intent": "memory_store", "contains": ["кедр-19"], "memory_changed": True},
            {"u": "Какой резервный маркер я просил запомнить?", "intent": "memory_recall", "contains": ["кедр-19"], "abstained": False},
            {"u": "Сбрось память.", "intent": "memory_clear", "contains": ["очищена"], "memory_changed": True},
            {"u": "Какой ключ проекта я просил сохранить?", "intent": "memory_recall", "contains": ["нет сохранённого значения"], "abstained": True},
        ],
    },
    {
        "id": "world_anaphora",
        "capability": "world_state",
        "turns": [
            {"u": "У МодульА теперь статус «ожидание».", "intent": "world_update", "contains": ["ожидание"], "memory_changed": True},
            {"u": "Каков статус МодульА?", "intent": "world_query", "contains": ["ожидание"], "abstained": False},
            {"u": "Теперь МодульА активен, обнови его статус.", "intent": "world_update", "contains": ["активен"], "memory_changed": True},
            {"u": "Каков его статус?", "intent": "world_query", "contains": ["активен"], "abstained": False},
            {"u": "У МодульБ теперь состояние «стоп».", "intent": "world_update", "contains": ["стоп"], "memory_changed": True},
            {"u": "Каково его состояние?", "intent": "world_query", "contains": ["стоп"], "abstained": False},
        ],
    },
    {
        "id": "causal_multihop",
        "capability": "causal",
        "turns": [
            {"u": "Перегрев приводит к деградации датчика.", "intent": "causal_store", "contains": ["перегрев", "деградации датчика"]},
            {"u": "Деградация датчика приводит к ошибке калибровки.", "intent": "causal_store", "contains": ["деградация датчика", "ошибке калибровки"]},
            {"u": "Ошибка калибровки приводит к ложной тревоге.", "intent": "causal_store", "contains": ["ошибка калибровки", "ложной тревоге"]},
            {"u": "Почему ложная тревога?", "intent": "causal_query", "contains": ["перегрев", "деградации датчика", "ошибке калибровки", "ложной тревоге"], "abstained": False},
            {"u": "Почему деградация датчика?", "intent": "causal_query", "contains": ["перегрев", "деградации датчика"], "abstained": False},
            {"u": "Почему потеря питания?", "intent": "causal_query", "contains": ["Данных недостаточно"], "abstained": True},
        ],
    },
    {
        "id": "relation_context",
        "capability": "relations",
        "turns": [
            {"u": "Ирина передала Максиму жетон.", "intent": "relation_transfer", "contains": ["Ирина", "Максиму", "жетон"]},
            {"u": "Кто передал жетон Максиму?", "intent": "relation_query", "contains": ["Ирина", "Максиму", "жетон"], "abstained": False},
            {"u": "Что произошло?", "intent": "context_explain", "contains": ["Ирина", "Максиму", "жетон"], "abstained": False},
            {"u": "Олег вручил Свете компас.", "intent": "relation_transfer", "contains": ["Олег", "Свете", "компас"]},
            {"u": "Кто передал компас Свете?", "intent": "relation_query", "contains": ["Олег", "Свете", "компас"], "abstained": False},
            {"u": "Что случилось?", "intent": "context_explain", "contains": ["Олег", "Свете", "компас"], "abstained": False},
        ],
    },
    {
        "id": "arithmetic_epistemic",
        "capability": "exact_evidence",
        "turns": [
            {"u": "Вычисли 37 * 19.", "intent": "arithmetic", "contains": ["703"], "abstained": False},
            {"u": "Посчитай (18 + 7) * 4.", "intent": "arithmetic", "contains": ["100"], "abstained": False},
            {"u": "Чему равно 144 / 12?", "intent": "arithmetic", "contains": ["12"], "abstained": False},
            {"u": "Данных нет о температуре на станции «Север-9».", "intent": "insufficient_evidence", "contains": ["Данных недостаточно"], "abstained": True},
            {"u": "Какие доказательства нужны для вывода?", "intent": "evidence_query", "contains": ["источники", "проверка"], "abstained": False},
            {"u": "Вычисли 2 ** 10.", "intent": "arithmetic", "contains": ["1024"], "abstained": False},
        ],
    },
    {
        "id": "world_revision",
        "capability": "world_revision",
        "turns": [
            {"u": "У узла Сигма теперь статус «проверка».", "intent": "world_update", "contains": ["проверка"]},
            {"u": "Каков статус узла Сигма?", "intent": "world_query", "contains": ["проверка"], "abstained": False},
            {"u": "У узла Сигма теперь статус «готов».", "intent": "world_update", "contains": ["готов"]},
            {"u": "Каков его статус?", "intent": "world_query", "contains": ["готов"], "abstained": False},
            {"u": "У узла Тау теперь статус «ошибка».", "intent": "world_update", "contains": ["ошибка"]},
            {"u": "Каков статус узла Тау?", "intent": "world_query", "contains": ["ошибка"], "abstained": False},
        ],
    },
    {
        "id": "memory_revision_history",
        "capability": "memory_revision",
        "turns": [
            {"u": "Запомни: приоритет = высокий.", "intent": "memory_store", "contains": ["высокий"]},
            {"u": "Какой приоритет я просил сохранить?", "intent": "memory_recall", "contains": ["высокий"], "abstained": False},
            {"u": "Запомни: приоритет = низкий.", "intent": "memory_store", "contains": ["низкий"]},
            {"u": "Какой приоритет я просил сохранить?", "intent": "memory_recall", "contains": ["низкий"], "abstained": False},
            {"u": "Что я сказал раньше?", "intent": "history_recall", "contains": ["Запомни: приоритет = низкий"], "abstained": False},
            {"u": "Сбрось память.", "intent": "memory_clear", "contains": ["очищена"]},
        ],
    },
    {
        "id": "epistemic_then_causal",
        "capability": "abstention",
        "turns": [
            {"u": "Нет источников о причине сбоя XJ-41.", "intent": "insufficient_evidence", "contains": ["Данных недостаточно"], "abstained": True},
            {"u": "Почему сбой XJ-41?", "intent": "causal_query", "contains": ["Данных недостаточно"], "abstained": True},
            {"u": "Шум вентилятора вызывает вибрацию корпуса.", "intent": "causal_store", "contains": ["шум вентилятора", "вибрацию корпуса"]},
            {"u": "Почему вибрация корпуса?", "intent": "causal_query", "contains": ["шум вентилятора", "вибрацию корпуса"], "abstained": False},
            {"u": "Информация отсутствует о внешнем датчике.", "intent": "insufficient_evidence", "contains": ["Данных недостаточно"], "abstained": True},
            {"u": "Какие доказательства нужны?", "intent": "evidence_query", "contains": ["источники", "противоречия"], "abstained": False},
        ],
    },
    {
        "id": "formal_logic",
        "capability": "formal",
        "turns": [
            {"u": "Если канал закрыт, то поток остановлен. канал закрыт. Что следует?", "intent": "formal_modus_ponens", "contains": ["поток остановлен"], "abstained": False},
            {"u": "Все инженеры являются специалистами. Некоторые исследователи являются инженерами.", "intent": "formal_some", "contains": ["Некоторые исследователи являются специалистами"], "abstained": False},
            {"u": "Вычисли 81 / 9.", "intent": "arithmetic", "contains": ["9"], "abstained": False},
            {"u": "Нет наблюдений о состоянии резервного канала.", "intent": "insufficient_evidence", "contains": ["Данных недостаточно"], "abstained": True},
            {"u": "Какие доказательства нужны для надёжного вывода?", "intent": "evidence_query", "contains": ["независимые источники"], "abstained": False},
            {"u": "Вычисли (11 - 3) * 7.", "intent": "arithmetic", "contains": ["56"], "abstained": False},
        ],
    },
    {
        "id": "mixed_long_context",
        "capability": "mixed",
        "turns": [
            {"u": "Запомни: кодовое слово метеор.", "intent": "memory_store", "contains": ["метеор"]},
            {"u": "У Реактор7 теперь статус «стабилен».", "intent": "world_update", "contains": ["стабилен"]},
            {"u": "Перегрузка сети приводит к задержке телеметрии.", "intent": "causal_store", "contains": ["перегрузка сети", "задержке телеметрии"]},
            {"u": "Напомни кодовое слово.", "intent": "memory_recall", "contains": ["метеор"], "abstained": False},
            {"u": "Почему задержка телеметрии?", "intent": "causal_query", "contains": ["перегрузка сети", "задержке телеметрии"], "abstained": False},
            {"u": "Каков его статус?", "intent": "world_query", "contains": ["стабилен"], "abstained": False},
        ],
    },
]


def norm(s: str) -> str:
    return str(s).casefold().replace("ё", "е")


def check(out, exp):
    failures = []
    if out.intent != exp["intent"]:
        failures.append(f"intent:{out.intent}!={exp['intent']}")
    text_n = norm(out.text)
    for needle in exp.get("contains", []):
        if norm(needle) not in text_n:
            failures.append(f"missing:{needle}")
    if "abstained" in exp and bool(out.abstained) != bool(exp["abstained"]):
        failures.append(f"abstained:{out.abstained}!={exp['abstained']}")
    if "memory_changed" in exp and bool(out.memory_changed) != bool(exp["memory_changed"]):
        failures.append(f"memory_changed:{out.memory_changed}!={exp['memory_changed']}")
    return failures


def main():
    script_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    rows = []
    scenario_scores = []
    cap = {}
    total = correct = 0
    designated_abstain = abstain_true_positive = abstain_false_positive = non_abstain_designated = 0

    for scenario in SCENARIOS:
        sid = "fresh-" + scenario["id"]
        mem = OUT / f"memory_{scenario['id']}.json"
        if mem.exists():
            mem.unlink()
        runtime = ExactCognitiveRussianRuntimeV2(memory_path=mem, artifact_root=None)
        s_ok = True
        for idx, exp in enumerate(scenario["turns"], 1):
            out = runtime.answer(exp["u"], session_id=sid)
            failures = check(out, exp)
            ok = not failures
            total += 1
            correct += int(ok)
            s_ok = s_ok and ok
            designated = exp.get("abstained") is True
            if designated:
                designated_abstain += 1
                abstain_true_positive += int(out.abstained)
            else:
                non_abstain_designated += 1
                abstain_false_positive += int(out.abstained)
            rows.append({
                "scenario": scenario["id"],
                "capability": scenario["capability"],
                "turn": idx,
                "user": exp["u"],
                "expected": exp,
                "response": asdict(out),
                "strict_ok": ok,
                "failures": failures,
            })
        scenario_scores.append({"scenario": scenario["id"], "all_turns_ok": s_ok})
        c = cap.setdefault(scenario["capability"], [0, 0])
        for r in rows[-len(scenario["turns"]):]:
            c[0] += 1
            c[1] += int(r["strict_ok"])

    payload = {
        "schema": "nexus.crc_r2.russian_dialogue_fresh.v1",
        "scientific_boundary": "Fresh deterministic Russian multi-turn benchmark of the existing R1.3-X Cognitive Russian Runtime V2 conversation core. No runtime tuning after benchmark freeze; exact external organs are not mounted in this run. This is not a free-form autoregressive LLM benchmark.",
        "benchmark_source_sha256": script_sha,
        "runtime": "ExactCognitiveRussianRuntimeV2",
        "artifact_root": None,
        "n_scenarios": len(SCENARIOS),
        "turns_per_scenario": 6,
        "n_turns": total,
        "strict_turn_accuracy": correct / total,
        "scenario_all_turns_accuracy": sum(x["all_turns_ok"] for x in scenario_scores) / len(scenario_scores),
        "abstention_recall": abstain_true_positive / max(1, designated_abstain),
        "false_abstention_rate": abstain_false_positive / max(1, non_abstain_designated),
        "by_capability": {k: {"n": v[0], "strict_accuracy": v[1] / v[0]} for k, v in sorted(cap.items())},
        "scenario_scores": scenario_scores,
        "rows": rows,
    }
    out = OUT / "FRESH_RUSSIAN_DIALOGUE_RESULT.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    (OUT / "FRESH_RUSSIAN_DIALOGUE_RESULT.sha256").write_text(f"{sha}  {out.name}\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("n_turns", "strict_turn_accuracy", "scenario_all_turns_accuracy", "abstention_recall", "false_abstention_rate", "by_capability")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
