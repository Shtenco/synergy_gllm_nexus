from nexus_gllm.compiler_ru import RussianGraphCompiler
from nexus_gllm.graph import DynamicHyperGraph
from nexus_gllm.temporal import EventGraphReasoner


def test_compiles_first_then_into_before_relation():
    graph = DynamicHyperGraph()
    compiler = RussianGraphCompiler()
    update = compiler.compile_event_statement("Сначала дождь начался, потом дорогу затопило.", graph)
    temporal = EventGraphReasoner(graph)
    a = temporal.ensure_event("дождь начался")
    b = temporal.ensure_event("дорогу затопило")
    assert temporal.before(a, b).holds is True
    assert update["relation"] == "before"


def test_compiles_poetomu_into_cause_relation():
    graph = DynamicHyperGraph()
    compiler = RussianGraphCompiler()
    update = compiler.compile_event_statement("Ливень усилился, поэтому дорогу затопило.", graph)
    temporal = EventGraphReasoner(graph)
    a = temporal.ensure_event("Ливень усилился")
    b = temporal.ensure_event("дорогу затопило")
    assert temporal.causes(a, b).holds is True
    assert update["relation"] == "causes"


def test_compiles_posle_into_before_relation():
    graph = DynamicHyperGraph()
    compiler = RussianGraphCompiler()
    compiler.compile_event_statement("После отключения света произошло отключение сервера.", graph)
    temporal = EventGraphReasoner(graph)
    a = temporal.ensure_event("отключения света")
    b = temporal.ensure_event("отключение сервера")
    assert temporal.before(a, b).holds is True


def test_compiles_temporal_and_causal_questions():
    compiler = RussianGraphCompiler()
    q1 = compiler.compile_event_question("Что было раньше: дождь начался или дорогу затопило?")
    assert q1.kind == "temporal_choice"
    assert q1.left == "дождь начался"
    assert q1.right == "дорогу затопило"

    q2 = compiler.compile_event_question("Что стало причиной дорогу затопило?")
    assert q2.kind == "cause_of"
    assert q2.target == "дорогу затопило"
