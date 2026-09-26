from __future__ import annotations

import ast
import json
import math
import operator
import re
import threading
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

from .r13x import Proposal, R13XGovernor, Verifier
try:
    from .r13x_hybrid_router import high_precision_gate
except Exception:
    high_precision_gate = lambda text: None


_WORD = re.compile(r"[A-Za-zА-Яа-яЁё0-9_%-]+", re.UNICODE)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().casefold().replace("ё", "е"))


def _cap(text: str) -> str:
    text = str(text or "").strip()
    return text[:1].upper() + text[1:] if text else text

def _stem_ru(word: str) -> str:
    w=_norm(word)
    for suf in ("иями","ями","ами","ого","ему","ыми","ими","ов","ев","ом","ем","ах","ях","ам","ям","ой","ей","ою","ею","ами","ями","ы","и","а","я","у","ю","е","о"):
        if len(w)>len(suf)+3 and w.endswith(suf):
            return w[:-len(suf)]
    return w


@dataclass
class ParsedRU:
    intent: str
    slots: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    normalized: str = ""


@dataclass
class CognitiveRUResponse:
    text: str
    intent: str
    confidence: float
    abstained: bool = False
    evidence: tuple[str, ...] = ()
    memory_changed: bool = False
    organ: str = "core"
    trace: tuple[str, ...] = ()


class PersistentDialogueMemory:
    """Small deterministic persistent memory. No hidden network calls."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._lock = threading.RLock()
        self._data: dict[str, dict[str, Any]] = {"sessions": {}}
        if self.path and self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._data = {"sessions": {}}

    def _session(self, session_id: str) -> dict[str, Any]:
        sessions = self._data.setdefault("sessions", {})
        return sessions.setdefault(session_id, {
            "kv": {}, "facts": [], "world": {}, "causal": [], "turns": []
        })

    def _flush(self):
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def remember(self, session_id: str, key: str, value: Any, *, source: str = "user"):
        with self._lock:
            s = self._session(session_id)
            s["kv"][_norm(key)] = {"value": value, "source": source}
            self._flush()

    def recall(self, session_id: str, key: str):
        with self._lock:
            return self._session(session_id)["kv"].get(_norm(key))

    def add_fact(self, session_id: str, subject: str, relation: str, obj: str):
        with self._lock:
            s = self._session(session_id)
            fact = {"subject": subject, "relation": relation, "object": obj}
            s["facts"].append(fact)
            self._flush()
            return fact

    def facts(self, session_id: str):
        with self._lock:
            return list(self._session(session_id)["facts"])

    def set_world(self, session_id: str, entity: str, attr: str, value: str):
        with self._lock:
            s = self._session(session_id)
            s["world"].setdefault(_norm(entity), {})[_norm(attr)] = value
            self._flush()

    def get_world(self, session_id: str, entity: str, attr: str):
        with self._lock:
            return self._session(session_id)["world"].get(_norm(entity), {}).get(_norm(attr))

    def add_causal(self, session_id: str, cause: str, effect: str):
        with self._lock:
            s = self._session(session_id)
            edge = {"cause": cause, "effect": effect}
            if edge not in s["causal"]:
                s["causal"].append(edge)
            self._flush()

    def causal_edges(self, session_id: str):
        with self._lock:
            return list(self._session(session_id)["causal"])

    def add_turn(self, session_id: str, role: str, text: str):
        with self._lock:
            s = self._session(session_id)
            s["turns"].append({"role": role, "text": text})
            s["turns"] = s["turns"][-100:]
            self._flush()

    def turns(self, session_id: str):
        with self._lock:
            return list(self._session(session_id)["turns"])

    def clear(self, session_id: str):
        with self._lock:
            self._data.setdefault("sessions", {})[session_id] = {
                "kv": {}, "facts": [], "world": {}, "causal": [], "turns": []
            }
            self._flush()


class RussianSemanticParser:
    """Deterministic Russian parser covering dialogue, memory, world and simple reasoning."""

    GREET = ("привет", "здравствуй", "здравствуйте", "добрый день", "добрый вечер")
    CAP = ("что ты умеешь", "что умеешь", "твои возможности", "кто ты", "что можешь")
    WHY = ("почему", "из-за чего", "по какой причине")

    def parse(self, text: str) -> ParsedRU:
        raw = str(text or "").strip()
        t = _norm(raw)
        if not t:
            return ParsedRU("empty", {}, 1.0, t)

        greet_t=t.strip(" .,!?:;")
        if any(greet_t == g or greet_t.startswith(g + " ") for g in self.GREET):
            return ParsedRU("greeting", {}, .99, t)
        if any(x in t for x in self.CAP):
            return ParsedRU("capabilities", {}, .99, t)
        if any(x in t for x in ("забудь эту сессию", "очисти память сессии", "сбрось память")):
            return ParsedRU("memory_clear", {}, .99, t)

        # Explicit memory commands.
        m = re.search(r"(?:запомни|сохрани|запиши|зафиксируй)\b(?:\s*[:,-])?\s*(.+)$", raw, re.I)
        if m:
            payload = m.group(1).strip().rstrip(".")
            km = re.match(r"(?P<key>[^:=—-]{2,80})\s*(?:=|:|—|-)\s*(?P<value>.+)", payload)
            if km:
                return ParsedRU("memory_store", {"key": km.group("key").strip(), "value": km.group("value").strip()}, .99, t)
            cm = re.search(r"кодовое\s+слово\s+(?P<value>[\wА-Яа-яЁё-]+)", payload, re.I)
            if cm:
                return ParsedRU("memory_store", {"key": "кодовое слово", "value": cm.group("value")}, .99, t)
            return ParsedRU("memory_store", {"key": "последняя заметка", "value": payload}, .93, t)

        if re.search(r"(?:какое|скажи|назови|напомни).*кодовое\s+слово", t):
            return ParsedRU("memory_recall", {"key": "кодовое слово"}, .99, t)
        m = re.search(r"какой\s+(?P<key>.+?)\s+я\s+(?:просил|просила)\s+(?:сохранить|запомнить|зафиксировать)", t)
        if m:
            return ParsedRU("memory_recall", {"key": m.group("key").strip()}, .94, t)
        m = re.search(r"(?:что|какое значение|что было).*?(?:запомнил|запомнила|сохранил|сохранила|записал|записала).*?(?:про|для)?\s*([^?]+)", t)
        if m:
            key=re.sub(r"^(?:про|для)\s+","",m.group(1).strip())
            return ParsedRU("memory_recall", {"key": key}, .90, t)
        if any(x in t for x in ("что я сказал раньше", "что я говорил раньше", "что было раньше", "что я сказал до этого")):
            return ParsedRU("history_recall", {}, .95, t)

        # World state.
        m = re.search(r"у\s+(?P<entity>[^:,.?]+?)\s+теперь\s+(?:статус|состояние)\s*[«\"']?(?P<value>[^.»\"'?!]+)", t)
        if m:
            return ParsedRU("world_update", {"entity":m.group("entity").strip(), "attr":"статус", "value":m.group("value").strip()}, .98, t)
        m = re.search(r"теперь\s+(?P<entity>[а-яa-z0-9_-]+)\s+(?P<value>[а-яa-z0-9_-]+),?\s+обнови\s+(?:его|ее|её)\s+(?:статус|состояние)", t)
        if m:
            return ParsedRU("world_update", {"entity":m.group("entity").strip(), "attr":"статус", "value":m.group("value").strip()}, .96, t)
        m = re.search(r"(?:статус|состояние)\s+(?P<entity>[^:,.?]+?)\s+(?:теперь|стал|стало|=|:)\s*(?P<value>[^.?!]+)", t)
        if m:
            return ParsedRU("world_update", {"entity":m.group("entity").strip(), "attr":"статус", "value":m.group("value").strip()}, .98, t)
        m = re.search(r"в\s+каком\s+состоянии\s+(?P<entity>[^?]+?)(?:\s+сейчас)?\??$", t)
        if m:
            return ParsedRU("world_query", {"entity":m.group("entity").strip(), "attr":"статус"}, .95, t)
        m = re.search(r"(?:какой|каково|что с)\s+(?:сейчас\s+)?(?:статус|состояние)?\s*(?P<entity>[^?]+)", t)
        if m and ("статус" in t or "состояни" in t):
            return ParsedRU("world_query", {"entity":m.group("entity").strip(), "attr":"статус"}, .94, t)

        # Causal statements and questions.
        m = re.search(r"(?P<cause>[^.?!]+?)\s+(?:вызывает|приводит к|является причиной)\s+(?P<effect>[^.?!]+)", t)
        if m:
            return ParsedRU("causal_store", {"cause":m.group("cause").strip(), "effect":m.group("effect").strip()}, .96, t)
        if any(t.startswith(x) for x in self.WHY):
            q = re.sub(r"^(почему|из-за чего|по какой причине)\s+", "", t).rstrip("?")
            q = re.sub(r"^(?:произош[её]л|произошла|возникает|возник|случился|случилась)\s+", "", q)
            return ParsedRU("causal_query", {"effect":q}, .90, t)

        # Safe arithmetic.
        if any(x in t for x in ("сколько", "вычисли", "посчитай", "рассчитай", "чему равна", "чему равно", "сумма", "разность", "произведение", "частное")):
            expr = self._extract_expression(t)
            if expr:
                return ParsedRU("arithmetic", {"expression":expr}, .99, t)

        # Simple Russian formal logic.
        m = re.search(r"если\s+(?P<a>.+?),\s*(?:то\s+)?(?P<b>.+?)\.\s*(?P=a)\.?\s*(?:что|следует|значит)", t)
        if m:
            return ParsedRU("formal_modus_ponens", {"premise":m.group("a"), "conclusion":m.group("b")}, .93, t)
        m = re.search(r"все\s+(?P<a>\w+)\s+(?:являются|это)\s+(?P<b>\w+).*некоторые\s+(?P<c>\w+)\s+(?:являются|это)\s+(?P<a2>\w+)", t)
        if m and _stem_ru(m.group("a"))==_stem_ru(m.group("a2")):
            return ParsedRU("formal_some", {"a":m.group("a"),"b":m.group("b"),"c":m.group("c")}, .90, t)

        # Transfer / receive relation variants.
        m = re.search(r"кто\s+(?:передал|вручил|дал)\s+(?P<obj>[А-Яа-яЁё-]+)\s+(?P<dst>[А-Яа-яЁё-]+)", raw, re.I)
        if m:
            return ParsedRU("relation_query", {"obj":m.group("obj"), "dst":m.group("dst")}, .92, t)
        patterns = [
            r"(?P<dst>[А-Яа-яЁё-]+)\s+получи(?:л|ла|ло|ли)\s+от\s+(?P<src>[А-Яа-яЁё-]+)\s+(?P<obj>[А-Яа-яЁё-]+)",
            r"(?P<src>[А-Яа-яЁё-]+)\s+(?:переда(?:л|ла|ло|ли)|вручи(?:л|ла|ло|ли))\s+(?P<dst>[А-Яа-яЁё-]+)\s+(?P<obj>[А-Яа-яЁё-]+)",
            r"(?P<obj>[А-Яа-яЁё-]+)\s+(?P<dst>[А-Яа-яЁё-]+)\s+да(?:л|ла)\s+(?P<src>[А-Яа-яЁё-]+)",
            r"от\s+(?P<src>[А-Яа-яЁё-]+)\s+(?P<dst>[А-Яа-яЁё-]+)\s+получи(?:л|ла)\s+(?P<obj>[А-Яа-яЁё-]+)",
            r"(?P<dst>[А-Яа-яЁё-]+)\s+получи(?:л|ла)\s+(?P<obj>[А-Яа-яЁё-]+)\s+от\s+(?P<src>[А-Яа-яЁё-]+)",
        ]
        for p in patterns:
            m = re.search(p, raw, re.I)
            if m:
                return ParsedRU("relation_transfer", {k:v for k,v in m.groupdict().items()}, .97, t)

        if "что произошло" in t or "что случилось" in t:
            return ParsedRU("context_explain", {}, .80, t)

        # Evidence / epistemic.
        if any(x in t for x in ("нет данных", "данных нет", "нет источников", "нет наблюдений", "информация отсутствует", "ничего не знаем", "источников нет", "информации мало")):
            return ParsedRU("insufficient_evidence", {}, .99, t)
        if any(x in t for x in ("какие доказательства", "достаточно ли доказательств", "источники", "проверить источник", "не выдумывать")):
            return ParsedRU("evidence_query", {}, .85, t)

        return ParsedRU("unknown", {}, .20, t)

    @staticmethod
    def _extract_expression(t: str) -> str | None:
        t=t.replace("×","*").replace("÷","/").replace("^","**")
        t=re.sub(r"(\\d+(?:[.,]\\d+)?)\\s+умножить\\s+на\\s+(\\d+(?:[.,]\\d+)?)", r"\\1*\\2", t)
        t=re.sub(r"(\\d+(?:[.,]\\d+)?)\\s+разделить\\s+на\\s+(\\d+(?:[.,]\\d+)?)", r"\\1/\\2", t)
        t=re.sub(r"сумма\\s+(\\d+(?:[.,]\\d+)?)\\s+и\\s+(\\d+(?:[.,]\\d+)?)", r"\\1+\\2", t)
        t=re.sub(r"разность\\s+(\\d+(?:[.,]\\d+)?)\\s+и\\s+(\\d+(?:[.,]\\d+)?)", r"\\1-\\2", t)
        t=re.sub(r"(сколько|будет|вычисли|посчитай|рассчитай|чему равно|равно)", " ", t)
        m=re.search(r"([0-9\s()+\-*/%.]{3,})", t)
        return re.sub(r"\s+","",m.group(1)) if m else None


class RussianRenderer:
    def render(self, kind: str, payload: dict[str, Any] | None = None) -> str:
        p=payload or {}
        if kind=="greeting":
            return "Привет! Я NEXUS R1.3-X. Могу работать с проверяемой памятью, состояниями, простой логикой, причинными связями и точными вычислениями."
        if kind=="capabilities":
            return ("Я NEXUS R1.3-X. Сейчас моё когнитивное ядро умеет работать с памятью сессии: сохранять и извлекать факты, отслеживать изменение состояния, "
                    "выполнять безопасные вычисления; логика и причинные связи обрабатываются отдельно, а при недостатке данных я отказываюсь от ответа, "
                    "если данных недостаточно.")
        if kind=="memory_saved":
            return f"Запомнил: {p['key']} — {p['value']}."
        if kind=="memory_recalled":
            return f"{_cap(p['key'])}: {p['value']}."
        if kind=="memory_missing":
            return f"В этой сессии у меня нет сохранённого значения для «{p['key']}»."
        if kind=="history":
            return p.get("text") or "В этой сессии пока нет предыдущих реплик."
        if kind=="world_updated":
            return f"Обновил состояние: {p['entity']} — {p['value']}."
        if kind=="world":
            return f"Текущее состояние «{p['entity']}»: {p['value']}."
        if kind=="relation":
            return f"{_cap(p['src'])} передал(а) {p['dst']} объект «{p['obj']}»."
        if kind=="arithmetic":
            return f"Результат: {p['value']}."
        if kind=="formal":
            return f"Да. Из заданных посылок следует: {p['conclusion']}."
        if kind=="causal_saved":
            return f"Зафиксировал причинную связь: {p['cause']} → {p['effect']}."
        if kind=="causal":
            return f"По сохранённой причинной модели: {p['cause']} приводит к «{p['effect']}»."
        if kind=="evidence_missing":
            return "Данных недостаточно для надёжного вывода. Я не буду придумывать ответ."
        if kind=="evidence":
            return "Для вывода нужны независимые источники, их происхождение и проверка на противоречия."
        if kind=="cleared":
            return "Память текущей сессии очищена."
        return "Я понял запрос неуверенно. Нужны дополнительные данные или более конкретная формулировка."


class ExactOrganHub:
    """Optional historical exact organs. Loaded only when real artifacts are present."""

    def __init__(self, artifact_root: str | Path | None = None):
        self.root=Path(artifact_root) if artifact_root else None
        self.organs: dict[str, Any]={}
        self.errors: dict[str, str]={}
        if self.root:
            self._load()

    def _try(self, name: str, fn):
        try:
            obj=fn()
            self.organs[name]=obj
        except Exception as e:
            self.errors[name]=f"{type(e).__name__}: {e}"

    def _load(self):
        from .unified_v3.moe.exact_experts import R76ExactExpert, R78ExactExpert, R710ExactExpert, R714ExactExpert
        p=self.root/"r76_semantic_knowledge_organ.pkl.bin"
        if p.is_file(): self._try("r76_semantic_memory", lambda:R76ExactExpert(p))
        r78=self.root/"nexus_moe_artifacts/r78/NEXUS_R78_TOP2_ARBITRATION_REAL_BLIND25_2026-08-20"
        if r78.is_dir(): self._try("r78_formal", lambda:R78ExactExpert(r78))
        r710=self.root/"nexus_moe_artifacts/r710/NEXUS_R710_PROOF_FIRST_FREEZE_2026-08-21"
        if r710.is_dir(): self._try("r710_proof", lambda:R710ExactExpert(r710))
        r714=self.root/"nexus_moe_artifacts/r714/NEXUS_R714_MULTILINGUAL_MORPHOLEX_FREEZE_2026-08-23"
        if r714.is_dir(): self._try("r714_morpholex", lambda:R714ExactExpert(r714))

    def status(self):
        return {"loaded":sorted(self.organs),"errors":dict(self.errors)}


class CognitiveRussianRuntime:
    def __init__(self, memory_path: str | Path | None = None, artifact_root: str | Path | None = None):
        self.parser=RussianSemanticParser()
        self.renderer=RussianRenderer()
        self.memory=PersistentDialogueMemory(memory_path)
        self.exact=ExactOrganHub(artifact_root)
        self.governor=R13XGovernor()
        self.verifier=Verifier()

    def answer(self, text: str, session_id: str = "default") -> CognitiveRUResponse:
        self.memory.add_turn(session_id,"user",text)
        p=self.parser.parse(text)
        trace=[f"intent={p.intent}",f"parser_conf={p.confidence:.2f}"]
        gate=high_precision_gate(text)
        if gate: trace.append(f"hybrid_gate={gate}")

        if p.intent=="greeting":
            return self._finish(session_id,p,self.renderer.render("greeting"),trace=trace)
        if p.intent=="capabilities":
            return self._finish(session_id,p,self.renderer.render("capabilities"),trace=trace)
        if p.intent=="memory_clear":
            self.memory.clear(session_id)
            return CognitiveRUResponse(self.renderer.render("cleared"),p.intent,p.confidence,memory_changed=True,trace=tuple(trace))
        if p.intent=="memory_store":
            self.memory.remember(session_id,p.slots["key"],p.slots["value"])
            return self._finish(session_id,p,self.renderer.render("memory_saved",p.slots),memory_changed=True,trace=trace)
        if p.intent=="memory_recall":
            item=self.memory.recall(session_id,p.slots["key"])
            if item:
                return self._finish(session_id,p,self.renderer.render("memory_recalled",{"key":p.slots["key"],"value":item["value"]}),evidence=("session_memory",),trace=trace)
            return self._finish(session_id,p,self.renderer.render("memory_missing",p.slots),abstained=True,trace=trace)
        if p.intent=="history_recall":
            turns=self.memory.turns(session_id)
            users=[x["text"] for x in turns[:-1] if x["role"]=="user"]
            substantive=[u for u in users if "?" not in u and not _norm(u).startswith(("напомни","какое","какой","что ","кто "))]
            chosen=(substantive[-1] if substantive else (users[-1] if users else ""))
            txt=f"Ранее вы сказали: «{chosen}»." if chosen else ""
            return self._finish(session_id,p,self.renderer.render("history",{"text":txt}),evidence=("dialogue_history",) if users else (),abstained=not bool(users),trace=trace)
        if p.intent=="world_update":
            self.memory.set_world(session_id,p.slots["entity"],p.slots["attr"],p.slots["value"])
            return self._finish(session_id,p,self.renderer.render("world_updated",p.slots),memory_changed=True,trace=trace)
        if p.intent=="world_query":
            v=self.memory.get_world(session_id,p.slots["entity"],p.slots["attr"])
            if v is not None:
                return self._finish(session_id,p,self.renderer.render("world",{"entity":p.slots["entity"],"value":v}),evidence=("world_state",),trace=trace)
            return self._finish(session_id,p,self.renderer.render("evidence_missing"),abstained=True,trace=trace)
        if p.intent=="relation_transfer":
            fact=self.memory.add_fact(session_id,p.slots["src"],"передать",p.slots["obj"])
            self.memory.remember(session_id,"последний факт",p.slots)
            return self._finish(session_id,p,self.renderer.render("relation",p.slots),memory_changed=True,evidence=("semantic_parser",),trace=trace)
        if p.intent=="relation_query":
            facts=self.memory.facts(session_id)
            obj=_norm(p.slots["obj"]); dst=_norm(p.slots["dst"])
            matches=[f for f in facts if _norm(f["object"])==obj]
            if matches:
                f=matches[-1]
                return self._finish(session_id,p,f"{_cap(f['subject'])} передал(а) {p.slots['dst']} объект «{p.slots['obj']}».",evidence=("session_memory","semantic_parser"),trace=trace)
            return self._finish(session_id,p,self.renderer.render("evidence_missing"),abstained=True,trace=trace)
        if p.intent=="context_explain":
            item=self.memory.recall(session_id,"последний факт")
            if item:
                return self._finish(session_id,p,self.renderer.render("relation",item["value"]),evidence=("session_memory","semantic_parser"),trace=trace)
            return self._finish(session_id,p,self.renderer.render("evidence_missing"),abstained=True,trace=trace)
        if p.intent=="causal_store":
            self.memory.add_causal(session_id,p.slots["cause"],p.slots["effect"])
            return self._finish(session_id,p,self.renderer.render("causal_saved",p.slots),memory_changed=True,trace=trace)
        if p.intent=="causal_query":
            effect=_norm(p.slots["effect"])
            edges=self.memory.causal_edges(session_id)
            def _tokset(x):
                return {w[:5] for w in re.findall(r"[а-яa-z0-9]+",_norm(x)) if len(w)>=3}
            et=_tokset(effect)
            matches=[e for e in edges if _norm(e["effect"]) in effect or effect in _norm(e["effect"]) or len(et & _tokset(e["effect"]))>=max(1,min(2,len(et)))]
            if matches:
                e=matches[-1]
                return self._finish(session_id,p,self.renderer.render("causal",e),evidence=("causal_memory",),trace=trace)
            return self._finish(session_id,p,self.renderer.render("evidence_missing"),abstained=True,trace=trace)
        if p.intent=="arithmetic":
            try:
                value=_safe_eval(p.slots["expression"])
                prop=Proposal("exact",value,.99,0.0,verification="EXACT_VERIFIED")
                chosen=self.governor.resolve([prop])
                return self._finish(session_id,p,self.renderer.render("arithmetic",{"value":chosen.value}),evidence=("exact_arithmetic",),organ="exact",trace=trace)
            except Exception:
                return self._finish(session_id,p,self.renderer.render("evidence_missing"),abstained=True,trace=trace)
        if p.intent=="formal_modus_ponens":
            return self._finish(session_id,p,self.renderer.render("formal",{"conclusion":p.slots["conclusion"]}),evidence=("formal_rule",),organ="formal",trace=trace)
        if p.intent=="formal_some":
            conclusion=f"Некоторые {p.slots['c']} являются {p.slots['b']}"
            return self._finish(session_id,p,self.renderer.render("formal",{"conclusion":conclusion}),evidence=("formal_rule",),organ="formal",trace=trace)
        if p.intent=="insufficient_evidence":
            return self._finish(session_id,p,self.renderer.render("evidence_missing"),abstained=True,organ="epistemic",trace=trace)
        if p.intent=="evidence_query":
            return self._finish(session_id,p,self.renderer.render("evidence"),organ="evidence",trace=trace)

        # Optional exact semantic organ can answer known frozen semantic atoms.
        r76=self.exact.organs.get("r76_semantic_memory")
        if r76 is not None:
            try:
                ans=r76.answer(text)
                if ans:
                    return self._finish(session_id,p,str(ans),evidence=("r76_exact",),organ="r76_semantic_memory",trace=trace+["r76_exact_hit"])
            except Exception:
                pass

        return self._finish(session_id,p,self.renderer.render("unknown"),abstained=True,trace=trace)

    def _finish(self, session_id: str, p: ParsedRU, text: str, *, abstained=False, evidence=(), memory_changed=False, organ="core", trace=()):
        self.memory.add_turn(session_id,"assistant",text)
        return CognitiveRUResponse(text,p.intent,p.confidence,abstained,tuple(evidence),memory_changed,organ,tuple(trace))


_ALLOWED_BIN={
    ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,
    ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,ast.Pow:operator.pow
}
_ALLOWED_UN={ast.UAdd:operator.pos,ast.USub:operator.neg}

def _safe_eval(expr: str):
    node=ast.parse(expr,mode="eval")
    def ev(n):
        if isinstance(n,ast.Expression): return ev(n.body)
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return n.value
        if isinstance(n,ast.BinOp) and type(n.op) in _ALLOWED_BIN:
            a,b=ev(n.left),ev(n.right)
            if abs(float(a))>1e12 or abs(float(b))>1e12: raise ValueError("too large")
            return _ALLOWED_BIN[type(n.op)](a,b)
        if isinstance(n,ast.UnaryOp) and type(n.op) in _ALLOWED_UN: return _ALLOWED_UN[type(n.op)](ev(n.operand))
        raise ValueError("unsafe expression")
    out=ev(node)
    if isinstance(out,float) and out.is_integer(): return int(out)
    return out
