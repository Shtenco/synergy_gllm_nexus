from nexus_gllm.research.query_graph import build_query_graph

def test_modes_and_world_probe():
    assert build_query_graph('2+2', {}, {}).mode == 'OFFLINE'
    assert build_query_graph('Найди последние новости OpenAI', {}, {}).mode == 'DEEP'
    assert build_query_graph('Кто написал Войну и мир?', {}, {}).mode == 'PROBE'
    assert build_query_graph('что угодно', {}, {'sealed': True}).mode == 'SEALED'
    assert build_query_graph('что угодно', {}, {'no_web': True}).mode == 'OFFLINE'