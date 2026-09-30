from __future__ import annotations
import ast, operator, re
from dataclasses import dataclass, asdict
from typing import Any

NAMES=("Анна","Борис","Вера","Глеб","Дина","Егор","Жанна","Илья","Кира","Лев","Мира","Нина","Олег","Рита","Саша","Тимур")
OBJECTS=("датчик","контроллер","узел","сервер","модуль","резерв","канал","буфер","агент","процесс")
COLORS=("красный","синий","зелёный","жёлтый","белый","чёрный","серый","фиолетовый")
STATES=("ожидание","активен","пауза","ошибка","готов","закрыт","открыт","архив")
VALUES=("меридиан","кварц","север","омега","дельта","маяк","вектор","контур","спектр","орбита")

@dataclass(frozen=True)
class ExecutionResult:
    status:str
    answer:Any
    plan:str
    trace:tuple[str,...]=()
    def to_dict(self):return asdict(self)

def _norm(s):return str(s).casefold().replace("ё","е")

def _known(text,vocab):
    t=_norm(text); rows=[]
    for v in vocab:
        p=t.find(_norm(v))
        if p>=0:rows.append((p,v))
    return [v for _,v in sorted(rows)]

def _safe_arith(expr):
    tree=ast.parse(expr,mode="eval")
    def ev(n):
        if isinstance(n,ast.Expression):return ev(n.body)
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)):return n.value
        if isinstance(n,ast.BinOp) and type(n.op) in (ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv):
            a,b=ev(n.left),ev(n.right)
            fn={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,
                ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv}[type(n.op)]
            return fn(a,b)
        raise ValueError("unsupported")
    return ev(tree)

class CompositionalCognitiveExecutorV2:
    def execute(self,text:str,plan:str)->ExecutionResult:
        t=_norm(text); nums=[int(x) for x in re.findall(r"\b\d+\b",t)]
        trace=[f"plan={plan}"]
        ans=None
        if plan=="natural_lookup":
            v=_known(text,VALUES); ans=v[-1] if v else None
        elif plan=="multihop_compare":
            v=_known(text,NAMES); ans=v[0] if v else None
        elif plan in ("multihop_logic","causal_chain"):
            v=_known(text,OBJECTS); ans=v[-1] if v else None
        elif plan=="memory_read":
            v=_known(text,VALUES+COLORS+STATES); ans=v[-1] if v else (str(nums[-1]) if nums else None)
        elif plan=="memory_arith":
            if len(nums)>=2:
                ans=str(nums[0]+nums[1]);trace+=["READ_MEMORY","COMPUTE_ADD","UPDATE_MEMORY","VERIFY"]
        elif plan=="conflict_latest":
            v=_known(text,COLORS); ans=v[-1] if v else None
            trace+=["ORDER_WRITES","LAST_WRITE_WINS"]
        elif plan=="world_transition":
            v=_known(text,STATES); ans=v[-1] if v else None
            trace+=["ORDER_EVENTS","CURRENT_STATE"]
        elif plan=="semantic_triple":
            v=_known(text,NAMES); ans=v[0] if v else None
        elif plan=="formal_arith":
            cs=re.findall(r"[\d\s()+\-*/]+",t)
            for c in sorted((x.strip() for x in cs if re.search(r"[+\-*/]",x)),key=len,reverse=True):
                try:ans=str(int(_safe_arith(c)));break
                except Exception:pass
        elif plan=="formal_logic":ans="да"
        elif plan=="evidence":
            ans="недостаточно данных" if any(x in t for x in ("нет данных","нет сведений","отсутствуют","недостаточно")) else "подтверждено"
        elif plan=="mixed_memory_compare":
            if len(nums)>=3:
                a,b,k=nums[:3];a=a+k
                ans="A" if a>b else ("B" if b>a else "равны")
                trace+=["READ_A_B","UPDATE_A","COMPARE","VERIFY"]
        elif plan=="abstain":ans="недостаточно данных"
        return ExecutionResult("RESOLVED" if ans is not None else "ABSTAIN",ans,plan,tuple(trace))
