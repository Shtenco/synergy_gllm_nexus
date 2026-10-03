from __future__ import annotations
import ast, operator, re
from dataclasses import dataclass, field


def _norm(s): return re.sub(r"\s+"," ",(s or "").strip().casefold().replace("ё","е"))
def _key(s): return " ".join(re.findall(r"[а-яa-z0-9_-]+",_norm(s)))
_ALLOWED={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,ast.Pow:operator.pow}
def _calc(expr):
    n=ast.parse(expr,mode="eval")
    def ev(x):
        if isinstance(x,ast.Expression): return ev(x.body)
        if isinstance(x,ast.Constant) and isinstance(x.value,(int,float)): return x.value
        if isinstance(x,ast.BinOp) and type(x.op) in _ALLOWED: return _ALLOWED[type(x.op)](ev(x.left),ev(x.right))
        raise ValueError("unsafe")
    y=ev(n); return int(y) if isinstance(y,float) and y.is_integer() else y

@dataclass(frozen=True)
class DialogueResponse:
    text:str; intent:str; abstained:bool=False; evidence:tuple[str,...]=(); memory_changed:bool=False
    provenance:tuple[str,...]=("r13x_v2_compat",)
@dataclass
class _Session:
    kv:dict=field(default_factory=dict); world:dict=field(default_factory=dict); causal:list=field(default_factory=list)
    relations:list=field(default_factory=list); turns:list=field(default_factory=list); focus:str|None=None

class R13XDialogueCompat:
    """Stateful compatibility layer for recovered R1.3-X V2 dialogue contracts.
    Not byte-identical historical R1.3-X; provenance remains explicit.
    """
    def __init__(self): self.sessions={}
    def _s(self,sid): return self.sessions.setdefault(sid,_Session())
    def answer(self,text,session_id="default",*,verified_text=None,verified_evidence=()):
        s=self._s(session_id); s.turns.append(("user",text)); t=_norm(text)
        def done(r): s.turns.append(("assistant",r.text)); return r
        if verified_text: return done(DialogueResponse(verified_text,"verified_crc",False,tuple(verified_evidence),False,("crc_verified","r13x_governor_compat")))
        if any(x in t for x in ("сбрось память","очисти память сессии","забудь эту сессию")):
            self.sessions[session_id]=_Session(); return DialogueResponse("Память текущей сессии очищена.","memory_clear",False,(),True)
        m=re.search(r"(?:запомни|сохрани|запиши|зафиксируй)\b(?:\s*[:,-—])?\s*(.+)$",text,re.I)
        if m:
            p=m.group(1).strip().rstrip("."); kv=re.match(r"([^:=—-]{2,80})\s*(?:=|:|—|-)\s*(.+)",p)
            if kv: k,v=kv.group(1).strip(),kv.group(2).strip()
            else:
                cm=re.search(r"кодовое\s+слово\s+([\wА-Яа-яЁё-]+)",p,re.I); k,v=("кодовое слово",cm.group(1)) if cm else ("последняя заметка",p)
            s.kv[_key(k)]=v; return done(DialogueResponse(f"Запомнил: {k} — {v}.","memory_store",False,(),True))
        if re.search(r"(?:какое|скажи|назови|напомни).*кодовое\s+слово",t):
            k="кодовое слово"; v=s.kv.get(_key(k)); return done(DialogueResponse(f"Кодовое слово: {v}." if v else f"В этой сессии у меня нет сохранённого значения для «{k}».","memory_recall",v is None,("session_memory",) if v else ()))
        m=re.search(r"какой\s+(.+?)\s+я\s+(?:просил|просила)\s+(?:сохранить|запомнить|зафиксировать)",t)
        if m:
            k=m.group(1).strip(); v=s.kv.get(_key(k)); return done(DialogueResponse(f"{k.capitalize()}: {v}." if v else f"В этой сессии у меня нет сохранённого значения для «{k}».","memory_recall",v is None,("session_memory",) if v else ()))
        m=re.search(r"у\s+([^:,.?]+?)\s+теперь\s+(?:статус|состояние)\s*[«\"']?([^.»\"'?!]+)",t) or re.search(r"теперь\s+([а-яёa-z0-9_-]+)\s+([а-яёa-z0-9_-]+),?\s+обнови\s+(?:его|ее|её)\s+(?:статус|состояние)",t)
        if m:
            e,v=m.group(1).strip(),m.group(2).strip(); s.world[_key(e)]=v; s.focus=e; return done(DialogueResponse(f"Обновил состояние: {e} — {v}.","world_update",False,(),True))
        if s.focus and re.search(r"(?:каков|каково|какой)\s+(?:его|ее|её)\s+(?:статус|состояние)",t):
            e=s.focus; v=s.world.get(_key(e)); return done(DialogueResponse(f"Текущее состояние «{e}»: {v}." if v else "Данных недостаточно для надёжного вывода. Я не буду придумывать ответ.","world_query",v is None,("world_state",) if v else ()))
        q=re.search(r"(?:какой|каков|каково|что с|в каком)\s+(?:сейчас\s+)?(?:статус|состоянии|состояние)?\s*([^?]+)",t)
        if q and ("статус" in t or "состояни" in t):
            e=q.group(1).strip(); v=s.world.get(_key(e)); return done(DialogueResponse(f"Текущее состояние «{e}»: {v}." if v else "Данных недостаточно для надёжного вывода. Я не буду придумывать ответ.","world_query",v is None,("world_state",) if v else ()))
        m=re.search(r"([^.?!]+?)\s+(?:вызывает|приводит к|является причиной)\s+([^.?!]+)",t)
        if m:
            edge=(m.group(1).strip(),m.group(2).strip());
            if edge not in s.causal: s.causal.append(edge)
            return done(DialogueResponse(f"Зафиксировал причинную связь: {edge[0]} → {edge[1]}.","causal_store",False,(),True))
        if t.startswith(("почему","из-за чего","по какой причине")):
            target=re.sub(r"^(почему|из-за чего|по какой причине)\s+","",t).rstrip("?")
            hit=next(((a,b) for a,b in reversed(s.causal) if _key(b) in _key(target) or _key(target) in _key(b)),None)
            if not hit: return done(DialogueResponse("Данных недостаточно для надёжного вывода. Я не буду придумывать ответ.","causal_query",True))
            path=[hit]; cur=_key(hit[0]); seen=set()
            while cur not in seen and len(path)<6:
                seen.add(cur); prev=next(((a,b) for a,b in reversed(s.causal) if _key(b)==cur),None)
                if not prev: break
                path.append(prev); cur=_key(prev[0])
            path.reverse(); parts=[path[0][0]]+[b for _,b in path]
            return done(DialogueResponse("Причинная цепочка: "+" → ".join(parts)+".","causal_query",False,("causal_memory","multi_hop")))
        m=re.search(r"кто\s+(?:передал|вручил|дал)\s+([А-Яа-яЁё-]+)\s+([А-Яа-яЁё-]+)",text,re.I)
        if m:
            obj,dst=m.group(1),m.group(2); hit=next((r for r in reversed(s.relations) if _norm(r["obj"])==_norm(obj) and _norm(r["dst"])==_norm(dst)),None)
            return done(DialogueResponse(f"{hit['src']} передал(а) {dst} объект «{obj}»." if hit else "Данных недостаточно для надёжного вывода. Я не буду придумывать ответ.","relation_query",hit is None,("session_memory","semantic_parser") if hit else ()))
        m=re.search(r"([А-Яа-яЁё-]+)\s+(?:переда(?:л|ла)|вручи(?:л|ла))\s+([А-Яа-яЁё-]+)\s+([А-Яа-яЁё-]+)",text,re.I)
        if m:
            r={"src":m.group(1),"dst":m.group(2),"obj":m.group(3)}; s.relations.append(r); s.focus=r["dst"]
            return done(DialogueResponse(f"{r['src']} передал(а) {r['dst']} объект «{r['obj']}».","relation_transfer",False,("semantic_parser",),True))
        if any(x in t for x in ("сколько","вычисли","посчитай","рассчитай","чему равно","чему равна")):
            z=t.replace("×","*").replace("÷","/").replace("^","**"); m=re.search(r"([0-9\s()+\-*/%.]{3,})",z)
            if m:
                try: return done(DialogueResponse(f"Результат: {_calc(re.sub(r'\s+','',m.group(1)))}.","arithmetic",False,("exact_arithmetic",)))
                except Exception: pass
        if any(x in t for x in ("нет данных","данных нет","нет источников","нет наблюдений","информация отсутствует","нет логов","логов нет")):
            return done(DialogueResponse("Данных недостаточно для надёжного вывода. Я не буду придумывать ответ.","insufficient_evidence",True))
        if any(x in t for x in ("что я сказал раньше","что я говорил раньше","что было раньше","что я сказал до этого")):
            users=[x[1] for x in s.turns[:-1] if x[0]=="user"]; v=users[-1] if users else ""
            return done(DialogueResponse(f"Ранее вы сказали: «{v}»." if v else "В этой сессии пока нет предыдущих реплик.","history_recall",not bool(v),("dialogue_history",) if v else ()))
        return done(DialogueResponse("Я понял запрос неуверенно. Нужны дополнительные данные или более конкретная формулировка.","unknown",True))
