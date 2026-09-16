from __future__ import annotations

from nexus_gllm.unified_v2.contracts import AnswerGraph


class NativeRussianSurfaceDecoderV2:
    """Deterministic faithful Russian renderer baseline.

    This organ has no factual authority: it only lexicalizes an AnswerGraph.
    A richer decoder may later replace it behind the same interface, but must
    continue to pass the semantic consistency guard.
    """

    RELATION_FORMS = {
        "отвечает_за": "отвечает за",
        "хранит": "хранит",
        "located_in": "находится в",
        "owned_by": "принадлежит",
        "is_a": "является",
        "before": "происходит до",
        "causes": "вызывает",
        "contains": "содержит",
    }

    @classmethod
    def _surface(cls, value) -> str:
        return value.canonical_name if hasattr(value, "canonical_name") else str(value)

    @classmethod
    def _relation(cls, relation: str) -> str:
        return cls.RELATION_FORMS.get(relation, relation.replace("_", " "))

    def render(self, answer_graph: AnswerGraph) -> str:
        if not answer_graph.claims:
            if answer_graph.abstentions:
                return " ".join(x.rstrip(". ") + "." for x in answer_graph.abstentions)
            return "Недостаточно данных."

        sentences: list[str] = []
        for claim in answer_graph.claims:
            subject = self._surface(claim.subject)
            obj = self._surface(claim.object)
            relation = self._relation(claim.relation)
            neg = "не " if claim.polarity == "negative" else ""
            sentences.append(f"{subject} {neg}{relation} {obj}.")

        if answer_graph.uncertainty:
            sentences.extend("Уточнение: " + x.rstrip(". ") + "." for x in answer_graph.uncertainty)
        return " ".join(sentences)
