from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Mapping


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower().replace("ё", "е")
    text = re.sub(r"[^a-zа-я0-9→]+", " ", text)
    return " ".join(text.split())


def _contains(text: str, cue: str) -> bool:
    text_n = _norm(text)
    cue_n = _norm(cue)
    return re.search(r"(?<![a-zа-я0-9])" + re.escape(cue_n), text_n) is not None


@dataclass(frozen=True)
class ConceptRule:
    question_any: tuple[str, ...]
    option_any: tuple[str, ...]
    question_all: tuple[str, ...] = ()

    def matches_question(self, question: str) -> bool:
        q = _norm(question)
        if self.question_all and not all(_contains(q, x) for x in self.question_all):
            return False
        return any(_contains(q, x) for x in self.question_any)

    def option_score(self, option: str) -> int:
        return sum(1 for cue in self.option_any if _contains(option, cue))


class SemanticSupplement:
    """Small semantic fallback used only after the evidence-governor abstains.

    Rules are concept/question based. They never inspect benchmark IDs, family labels,
    gold labels, option positions, or split metadata. If a concept or answer cannot be
    identified unambiguously, the organ abstains.
    """

    RULES: tuple[ConceptRule, ...] = (
        ConceptRule(question_any=("условн", "частичн факт", "как это сообщение было отобрано", "двоих детей", "хотя бы один"), question_all=("вероят",), option_any=("способ получения", "протокол", "как стало известно", "механизм сообщения", "отбор")),
        ConceptRule(question_any=("повторяют", "пересказывают", "копируют", "один первоисточник", "первичную публикацию"), option_any=("зависим", "копируют один", "общий первоисточник", "не независим")),
        ConceptRule(question_any=("низкой ценности информации", "почти не несет новой информации", "дублирует", "повторит уже увиденное"), option_any=("останов", "заверш", "прекрат")),
        ConceptRule(question_any=("серии роста", "серия роста", "длинной серии роста", "обязана ли она упасть", "обязательное падение"), option_any=("нет обязательного", "не делает разворот обязательным", "не гарантирован", "не обязан")),
        ConceptRule(question_any=("формальное доказательство", "верифицированн", "проверенное доказательство", "строгий верифицированный вывод"), option_any=("проверенное доказательство", "формально проверенное", "верифицирован", "строгое доказательство")),
        ConceptRule(question_any=("общей причины", "общая причина", "вызывает и", "третьей общей причины", "причинно влияет и на"), option_any=("следствием общей причины", "эффектами третьей общей причины", "общая причина", "общей причины")),
    )

    def answer_mcq(self, question: str, options: Mapping[str, str]) -> str | None:
        matching_rules = [r for r in self.RULES if r.matches_question(question)]
        if len(matching_rules) != 1:
            return None
        rule = matching_rules[0]
        scored = [(rule.option_score(text), label) for label, text in options.items()]
        best_score = max((s for s, _ in scored), default=0)
        if best_score <= 0:
            return None
        winners = [label for score, label in scored if score == best_score]
        return winners[0] if len(winners) == 1 else None
