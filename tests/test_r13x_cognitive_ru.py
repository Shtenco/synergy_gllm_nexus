from pathlib import Path
from nexus_gllm.r13x_cognitive_ru import CognitiveRussianRuntime, RussianSemanticParser, _safe_eval

def test_parser_handles_russian_transfer_variants():
    p=RussianSemanticParser()
    samples=[
      "Борис получил от Анны ключ.",
      "Мария получила от Ивана книгу.",
      "Анна передала Борису ключ.",
      "Ключ Борису дала Анна.",
      "От Анны Борис получил ключ.",
      "Борис получил ключ от Анны.",
    ]
    assert all(p.parse(x).intent=="relation_transfer" for x in samples)

def test_multiturn_memory(tmp_path:Path):
    r=CognitiveRussianRuntime(tmp_path/"mem.json")
    a=r.answer("Запомни: кодовое слово Север.","s")
    b=r.answer("Какое кодовое слово?","s")
    assert "Север" in a.text and "Север" in b.text

def test_world_revision(tmp_path:Path):
    r=CognitiveRussianRuntime(tmp_path/"mem.json")
    r.answer("Статус заказа теперь оплачен.","s")
    r.answer("Статус заказа теперь отменён.","s")
    q=r.answer("Какой сейчас статус заказа?","s")
    assert "отмен" in q.text.casefold()

def test_relation_followup(tmp_path:Path):
    r=CognitiveRussianRuntime(tmp_path/"mem.json")
    a=r.answer("Анна передала Борису ключ.","s")
    b=r.answer("Что произошло?","s")
    for t in ("анна","борис","ключ"):
        assert t in a.text.casefold()
        assert t in b.text.casefold()

def test_no_hallucination(tmp_path:Path):
    r=CognitiveRussianRuntime(tmp_path/"mem.json")
    q=r.answer("Нет данных о точном пароле сервера.","s")
    assert q.abstained
    assert "недостаточно" in q.text.casefold()

def test_safe_arithmetic():
    assert _safe_eval("(12+8)*3")==60
