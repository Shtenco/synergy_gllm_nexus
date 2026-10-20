from __future__ import annotations

import pytest

from nexus_gllm.v25_morph_router import RussianMorphRouter


def verified_fact(router, subject="Компания", relation="located_in",
                  obj="Казани", topic="default"):
    router.add_verified_fact(
        subject, relation, obj, provenance="demo:evidence:1",
        authority="evidence_governor", topic=topic,
    )


class FakeMorphology:
    def canonicalize(self, text, lang=None):
        assert lang == "ru"
        return text.replace("кредитная организация", "банк")

    def analyze(self, text, lang=None):
        return {"tokens": text.split()}


def test_fact_render_is_evidence_grounded():
    rt = RussianMorphRouter()
    verified_fact(rt)
    res = rt.answer("Где находится компания?")
    assert res.status == "verified"
    assert res.route == "fact"
    assert "Казани" in res.text
    assert "demo:evidence:1" in res.trace[-1]


def test_no_evidence_no_factual_answer():
    rt = RussianMorphRouter()
    res = rt.answer("Где находится компания?")
    assert res.status == "unverified"
    assert res.text == rt.NO_ANSWER


def test_provenance_and_authority_required():
    rt = RussianMorphRouter()
    with pytest.raises(ValueError):
        rt.add_verified_fact("А", "located_in", "Б", provenance="", authority="evidence_governor")
    with pytest.raises(ValueError):
        rt.add_verified_fact("А", "located_in", "Б", provenance="source", authority="model_guess")
    with pytest.raises(ValueError):
        rt.add_verified_qa("Вопрос", "Ответ", provenance="trace", authority="v24")


def test_normalization_uses_morphology_without_fake_source():
    rt = RussianMorphRouter(morphology=FakeMorphology())
    verified_fact(rt, subject="Банк", obj="Уфе")
    res = rt.answer("Где находится кредитная организация?")
    assert res.status == "verified"
    assert res.morphology_active
    assert "Уфе" in res.text


def test_conflicting_verified_facts_abstain():
    rt = RussianMorphRouter()
    verified_fact(rt, obj="Казани")
    verified_fact(rt, obj="Самаре")
    res = rt.answer("Где находится компания?")
    assert res.status == "conflict"
    assert res.text == rt.AMBIGUOUS


def test_exact_verified_qa_uses_existing_russian_answer():
    rt = RussianMorphRouter()
    rt.add_verified_qa("Что такое нейронная сеть?", "Нейронная сеть — вычислительная модель.",
                       provenance="curated:1", authority="evidence_governor")
    res = rt.answer("что такое нейронная сеть?")
    assert res.text == "Нейронная сеть — вычислительная модель."
    assert res.status == "verified"
    assert res.route == "exact_qa"


def test_conflicting_verified_qa_abstains():
    rt = RussianMorphRouter()
    rt.add_verified_qa("Что такое X?", "Это A.", provenance="one", authority="formal_authority")
    rt.add_verified_qa("Что такое X?", "Это B.", provenance="two", authority="formal_authority")
    assert rt.answer("Что такое X?").status == "conflict"


def test_ambiguous_anaphora_requires_clarification():
    rt = RussianMorphRouter()
    rt.mention("альфа", "Альфа", gender="f")
    rt.mention("бета", "Бета", gender="f")
    assert rt.answer("Где находится она?").status == "clarification"


def test_unique_anaphora_topic_scoped():
    rt = RussianMorphRouter()
    verified_fact(rt, subject="Банк", obj="Омске")
    rt.mention("банк", "Банк", gender="m")
    res = rt.answer("Где находится он?")
    assert res.status == "verified"
    assert "Омске" in res.text
    rt.topic_boundary("новая_тема")
    assert rt.answer("Где находится он?", topic="новая_тема").status == "clarification"


def test_llm_is_not_factual_authority_without_verifier():
    rt = RussianMorphRouter(v24_generate=lambda _: "Заведомо неподтверждённое утверждение.")
    res = rt.answer("Что случилось?")
    assert res.status == "unverified"
    assert "v24:rejected" in res.trace


def test_caller_verifier_can_promote_v24_candidate():
    rt = RussianMorphRouter(
        v24_generate=lambda _: "Подтверждённый ответ.",
        candidate_verifier=lambda q, a: q == "Проверить?" and a == "Подтверждённый ответ.",
    )
    res = rt.answer("Проверить?")
    assert res.status == "externally_verified"
    assert res.source == "v24+external_verifier"


def test_bad_morph_adapter_fails_closed():
    class BrokenMorph:
        def canonicalize(self, text, lang=None):
            raise RuntimeError("broken")
    rt = RussianMorphRouter(morphology=BrokenMorph())
    res = rt.answer("Как дела?")
    assert res.status == "error"
    assert res.text == rt.NO_ANSWER


def test_evil_morph_adapter_cannot_be_combined_with_pinned_artifact():
    with pytest.raises(ValueError):
        RussianMorphRouter(morph_root="/not/a/folder", morphology=FakeMorphology())


def test_empty_query_abstains():
    rt = RussianMorphRouter()
    assert rt.answer(" ").status == "abstain"
