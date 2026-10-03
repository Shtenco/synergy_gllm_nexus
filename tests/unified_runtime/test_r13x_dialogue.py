from nexus_gllm.unified_runtime.r13x_dialogue import R13XDialogueCompat

def test_memory_clear_world_anaphora_and_causal_chain():
    d=R13XDialogueCompat(); sid="s"
    assert "орбита-47" in d.answer("Запомни: ключ проекта = орбита-47.",sid).text
    assert "орбита-47" in d.answer("Какой ключ проекта я просил сохранить?",sid).text
    d.answer("У МодульА теперь статус активен.",sid)
    assert "активен" in d.answer("Каков его статус?",sid).text
    d.answer("Перегрев приводит к деградации.",sid); d.answer("Деградация приводит к ошибке.",sid)
    x=d.answer("Почему ошибка?",sid)
    assert "Перегрев" in x.text or "перегрев" in x.text
    d.answer("Сбрось память.",sid)
    assert d.answer("Какой ключ проекта я просил сохранить?",sid).abstained

def test_relation_arithmetic_and_epistemic_abstention():
    d=R13XDialogueCompat(); sid="r"
    d.answer("Ирина передала Павлу ключ.",sid)
    assert "Ирина" in d.answer("Кто передал ключ Павлу?",sid).text
    assert "42" in d.answer("Вычисли 6 * 7",sid).text
    assert d.answer("Нет данных о температуре.",sid).abstained
