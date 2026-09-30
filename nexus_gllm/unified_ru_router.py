from __future__ import annotations
import re
from pathlib import Path
import torch

from .r13x_trainable import LABELS, TrainableR13XRouter, vectorize

class UnifiedRURouter:
    """High-precision deterministic routing with learned fallback.

    The learned checkpoint uses the exact TrainableR13XRouter architecture.
    Deterministic gates own safety-critical / high-precision cases; the neural
    router is only a fallback for ambiguous Russian formulations.
    """
    def __init__(self, checkpoint: str | Path):
        d=torch.load(Path(checkpoint),map_location="cpu")
        dim=int(d.get("dim",512))
        self.model=TrainableR13XRouter(dim=dim)
        self.model.load_state_dict(d["state_dict"])
        self.model.eval()
        self.dim=dim

    @staticmethod
    def gate(text:str):
        t=text.casefold().replace("ё","е")
        noev=any(q in t for q in (
            "нет данных","данных нет","нет наблюден","без измерен","нет измерен",
            "без доступа","исходных данных вообще нет","неизвестном значении",
            "сведений","недостаточно","ничего не известно"))
        demand=any(q in t for q in (
            "точн","достоверн","гарантирован","назови","укажи","вывод","можно ли"))
        if noev and demand:return "abstain"
        if re.search(r"\d\s*[×*+/^-]\s*\(?\d",t) or any(q in t for q in (
            "умнож","целочисленн","вычесть","остаток","арифмет","числовой результат")):
            return "exact"
        if any(q in t for q in (
            "причин","принудительно отключ","каузал","корреляц",
            "совместной изменчивости","интервен","вмешательств")):return "causal"
        if any(q in t for q in (
            "сохран","запом","прежнее значение","верни именно сохран","памят","перезапиши")):
            return "memory"
        if any(q in t for q in (
            "актуально сейчас","историческое состояние","текущее состояние",
            "timeline","состояние актуально","сначала был","переходов")):return "world"
        if any(q in t for q in (
            "логическ","следует","обязано ли","посыл","=>","докаж",
            "выводится ли","импликац")):return "formal"
        if any(q in t for q in (
            "свидетельств","источник","неподтвержден","доказательств",
            "provenance","обоснован","наблюдаемое доказательство")):return "evidence"
        if any(q in t for q in (
            "кто действует","смысловую тройку","субъект","отношение","семантическ",
            "нормализуй смысл","смысловые роли")):return "semantic"
        if any(q in t for q in (
            "по-русски","граммат","канцеляр","естественным","исправь",
            "сохрани смысл","хорошем русском")):return "language"
        return None

    @torch.no_grad()
    def route(self,text:str):
        g=self.gate(text)
        if g is not None:return g,1.0,"authority_gate"
        logits=self.model(vectorize(text,self.dim).unsqueeze(0))[0]
        p=torch.softmax(logits,0)
        i=int(p.argmax())
        return LABELS[i],float(p[i]),"learned_fallback"
